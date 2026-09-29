"""Adapters retain published implementation identities and train within each fold."""
import numpy as np
from .base import Model


class ChempropModel(Model):
    def __init__(self,config,task,cache_root): self.config,self.task=dict(config),task

    def _loader(self,smiles,y=None,shuffle=False):
        from chemprop import data,featurizers
        points=[data.MoleculeDatapoint.from_smi(s,y=None if y is None else y[i],ignore_stereo=False) for i,s in enumerate(smiles)]
        ds=data.MoleculeDataset(points,featurizer=featurizers.SimpleMoleculeMolGraphFeaturizer())
        return data.build_dataloader(ds,batch_size=self.config.get('batch_size',64),shuffle=shuffle,num_workers=0,seed=self.config.get('seed',42),drop_last=False)

    def fit(self,dataset,split=None,configuration=None):
        import torch
        from lightning import pytorch as pl
        from chemprop import models,nn
        if split is not None: dataset=dataset.subset(split)
        if configuration: self.config.update(configuration)
        if np.any(dataset.censoring!='exact'): raise ValueError('This Chemprop adapter requires exact observations; no censored-value substitution')
        pl.seed_everything(self.config.get('seed',42),workers=True)
        torch.set_num_threads(self.config.get('threads',4))
        width=self.config.get('width',300)
        mp=nn.BondMessagePassing(d_h=width,depth=self.config.get('depth',3),dropout=self.config.get('dropout',.1))
        head_type=nn.BinaryClassificationFFN if self.task=='classification' else nn.RegressionFFN
        head=head_type(n_tasks=len(dataset.labels),input_dim=width,hidden_dim=width)
        self.model=models.MPNN(mp,nn.MeanAggregation(),head,batch_norm=False,warmup_epochs=0)
        self.training_ids=dataset.ids.tolist();self.training_groups=set(dataset.groups);self.labels=dataset.labels
        self.mean=np.nanmean(dataset.y,axis=0) if self.task=='regression' else np.zeros(len(self.labels))
        self.scale=np.maximum(np.nanstd(dataset.y,axis=0),.1) if self.task=='regression' else np.ones(len(self.labels))
        self._trainer().fit(self.model,self._loader(dataset.smiles,(dataset.y-self.mean)/self.scale,True))
        self.model.eval()
        return self

    def _trainer(self):
        from lightning import pytorch as pl
        return pl.Trainer(accelerator=self.config.get('device','cpu'),devices=1,max_epochs=self.config.get('epochs',50),
                          logger=False,enable_checkpointing=False,enable_progress_bar=False,enable_model_summary=False,num_sanity_val_steps=0)

    def predict(self,molecules,context=None):
        import torch
        values=self._trainer().predict(self.model,self._loader(molecules))
        return torch.cat(values).numpy()*self.scale+self.mean

    def embed(self,molecules):
        import torch
        self.model.eval();values=[]
        with torch.no_grad():
            for batch in self._loader(molecules): values.append(self.model.fingerprint(batch.bmg,batch.V_d,batch.X_d).numpy())
        return np.concatenate(values)


class OpenPOMModel(Model):
    def __init__(self,config,task,cache_root):
        if task!='classification': raise ValueError('Published OpenPOM reproduction is a descriptor baseline; threshold transfer requires a separate experiment')
        self.config,self.task=dict(config),task

    def _features(self,smiles):
        from openpom.feat.graph_featurizer import GraphFeaturizer
        return GraphFeaturizer().featurize(smiles)

    def fit(self,dataset,split=None,configuration=None):
        import deepchem as dc
        from openpom.models.mpnn_pom import MPNNPOMModel
        if split is not None: dataset=dataset.subset(split)
        if configuration: self.config.update(configuration)
        from openpom.feat.graph_featurizer import GraphConvConstants
        weights=np.isfinite(dataset.y).astype(float)
        ds=dc.data.NumpyDataset(X=self._features(dataset.smiles),y=np.nan_to_num(dataset.y),w=weights,ids=dataset.ids)
        self.training_ids=dataset.ids.tolist(); self.training_groups=set(dataset.groups); self.labels=dataset.labels
        self.model=MPNNPOMModel(n_tasks=len(self.labels),batch_size=self.config.get('batch_size',64),mode='classification',
            number_atom_features=GraphConvConstants.ATOM_FDIM,number_bond_features=GraphConvConstants.BOND_FDIM,
            node_out_feats=self.config.get('width',100),edge_hidden_feats=75,num_step_message_passing=self.config.get('depth',5),
            ffn_hidden_list=[392,392],ffn_dropout_p=self.config.get('dropout',.12),learning_rate=self.config.get('learning_rate',.001),
            loss_aggr_type='sum',device_name=self.config.get('device','cpu'),log_frequency=100)
        self.model.fit(ds,nb_epoch=self.config.get('epochs',60))
        return self

    def predict(self,molecules,context=None):
        import deepchem as dc
        p=np.asarray(self.model.predict(dc.data.NumpyDataset(X=self._features(molecules))))
        return p[:,:,1] if p.ndim==3 and p.shape[-1]==2 else p.reshape(len(molecules),len(self.labels))

    def embed(self,molecules):
        import deepchem as dc
        return np.asarray(self.model.predict_embedding(dc.data.NumpyDataset(X=self._features(molecules))))
