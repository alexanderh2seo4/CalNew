"""Pinned pretrained encoders with independently cached, frozen representations.

Only the implemented frozen route is accepted. Unsupported adaptation requests fail
explicitly rather than silently running a frozen model under a fine-tuning label.
"""
from pathlib import Path
import numpy as np

from ..chemistry import identify
from ..io import digest, file_digest, write_json
from .classical import ClassicalModel


class PretrainedModel(ClassicalModel):
    def __init__(self,config,task,cache_root):
        super().__init__({**config,'estimator':config.get('estimator','linear')},task,cache_root)
        if config.get('adaptation',config.get('mode','frozen'))!='frozen':
            raise NotImplementedError('This adapter implements frozen embeddings only; adapted checkpoints require a separate fold-trained adapter')
        self.cache_root=Path(cache_root)/config['family']
        self.cache_root.mkdir(parents=True,exist_ok=True)
        if config['family']=='unimol2':
            defaults={'revision':'bf37d253c0f5ac61f468137eb00059978a104ff0','model_size':'84m','pooling':'mean','append_chirality':True,
                      'conformer_seed':42,'generated_conformers':32,'retained_conformers':16}
            for key,value in defaults.items(): self.config.setdefault(key,value)

    def embed(self,molecules):
        canonical=[identify(s).smiles for s in molecules]
        settings={k:v for k,v in self.config.items() if k in ('family','checkpoint','revision','model_size','pooling','conformer_seed','generated_conformers','retained_conformers','append_chirality')}
        if self.config['family']=='molformer' and not self.config.get('revision'):
            raise ValueError('MoLFormer requires an immutable checkpoint revision')
        paths=[self.cache_root/(digest(dict(smiles=s,settings=settings))+'.npy') for s in canonical]
        missing=list(dict.fromkeys(s for s,p in zip(canonical,paths) if not p.exists()))
        if missing:
            values=self._molformer(missing) if self.config['family']=='molformer' else self._unimol(missing)
            for s,value in zip(missing,values):
                p=self.cache_root/(digest(dict(smiles=s,settings=settings))+'.npy')
                np.save(p,np.asarray(value,dtype=np.float32),allow_pickle=False)
                write_json(p.with_suffix('.json'),dict(smiles=s,settings=settings,training='unlabelled pretraining; frozen for all folds',feature_sha256=file_digest(p)))
        return np.stack([np.load(p,allow_pickle=False) for p in paths])

    def _molformer(self,smiles):
        import torch
        from transformers import AutoModel,AutoTokenizer
        checkpoint=self.config.get('checkpoint','ibm-research/MoLFormer-XL-both-10pct')
        kwargs=dict(revision=self.config['revision'],trust_remote_code=True,cache_dir=str(Path('data/checkpoints').resolve()))
        if getattr(self,'_molformer_loaded',None) is None:  # load once per adapter instance
            self._molformer_loaded=(AutoTokenizer.from_pretrained(checkpoint,**kwargs),
                                    AutoModel.from_pretrained(checkpoint,deterministic_eval=True,**kwargs).eval())
        tokenizer,model=self._molformer_loaded
        device=self.config.get('device','cpu'); model.to(device); torch.set_num_threads(self.config.get('threads',4))
        rows=[]
        # Published tokenizer/checkpoint may discard stereo tokens; preserve provenance and
        # compare the explicit chirality feature ablation rather than assuming sensitivity.
        for start in range(0,len(smiles),self.config.get('embedding_batch_size',16)):
            batch=smiles[start:start+self.config.get('embedding_batch_size',16)]
            tokens=tokenizer(batch,padding=True,truncation=False,return_tensors='pt')
            if tokens['input_ids'].shape[1]>202: raise ValueError('MoLFormer token length exceeds checkpoint training range')
            if tokenizer.unk_token_id is not None and (tokens['input_ids']==tokenizer.unk_token_id).any():
                raise ValueError('Unsupported SMILES token; chemical language branch unavailable')
            with torch.no_grad():
                output=model(**{k:v.to(device) for k,v in tokens.items()})
                rows.extend(output.pooler_output.cpu().numpy())
        return rows

    def _unimol(self,smiles):
        import torch
        from unimol_tools import UniMolRepr
        from huggingface_hub import hf_hub_download
        from ..conformers import conformer_arrays
        torch.set_num_threads(self.config.get('threads',4))
        revision=self.config.get('revision','bf37d253c0f5ac61f468137eb00059978a104ff0')
        size=self.config.get('model_size','84m')
        filename={'84m':'84M','164m':'164M','310m':'310M','570m':'570M','1.1B':'1.1B'}[size]
        weights=hf_hub_download('dptech/Uni-Mol2',f'modelzoo/{filename}/checkpoint.pt',revision=revision,
                                cache_dir=str(Path('data/checkpoints').resolve()))
        write_json(self.cache_root/'checkpoint.json',{'repository':'dptech/Uni-Mol2','revision':revision,'sha256':file_digest(weights),'size':size})
        model=UniMolRepr(data_type='molecule',model_name='unimolv2',model_size=self.config.get('model_size','84m'),
                         remove_hs=False,use_cuda=self.config.get('device','cpu')=='cuda',batch_size=4,pretrained_model_path=weights)
        rows=[]
        for s in smiles:
            atoms,coords,manifest=conformer_arrays(s,seed=self.config.get('conformer_seed',42),
                generated=self.config.get('generated_conformers',32),retained=self.config.get('retained_conformers',16))
            if self.config.get('pooling','mean')=='single': coords=coords[:1]
            elif self.config.get('pooling','mean')!='mean': raise NotImplementedError('Only single and mean conformer pooling are implemented')
            output=model.get_repr({'atoms':[atoms]*len(coords),'coordinates':list(coords)})
            embeddings=np.asarray(output['cls_repr'] if isinstance(output,dict) else output)
            row=embeddings.mean(axis=0)
            if self.config.get('append_chirality',True):
                from ..chemistry import fingerprints
                row=np.concatenate([row,fingerprints([s],size=256)[0]])
            rows.append(row)
        return rows
