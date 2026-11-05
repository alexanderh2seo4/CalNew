#!/usr/bin/env python3
"""Reconstruct an Olfr73 ligand-based pharmacophore, without the unavailable Phase model.

Everything rendered is derived from this calculation. Assay labels never enter training,
alignment, conformer selection or score settings; they are used only in final evaluation.
"""
import argparse, csv, hashlib, json, math, pathlib, platform, sys, time
import numpy as np
import scipy
from scipy.optimize import linear_sum_assignment, minimize
from scipy.spatial.transform import Rotation
from scipy.stats import spearmanr
from rdkit import Chem, RDConfig, rdBase
from rdkit.Chem import AllChem, ChemicalFeatures, Descriptors, rdMolDescriptors
from rdkit.Chem.EnumerateStereoisomers import EnumerateStereoisomers, StereoEnumerationOptions
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

P=pathlib.Path(__file__).resolve().parent
OUT=P/'outputs'; OUT.mkdir(exist_ok=True)
FACTORY=ChemicalFeatures.BuildFeatureFactory(str(pathlib.Path(RDConfig.RDDataDir)/'BaseFeatures.fdef'))
COLORS={'Donor':'#2563eb','Acceptor':'#ef4444','Hydrophobe':'#16a34a','Aromatic':'#d97706'}
PARAMS={'conformers_requested_per_stereoisomer':48,'seed':730019,'prune_rms_A':0.25,'energy_window_kcal_mol':6.0,'mmff_variant':'MMFF94s','mmff_max_iterations':1000,'training_matching_cutoff_A':1.8,'minimum_training_support':0.4,'radius_floor_A':0.75,'radius_dispersion_multiplier':1.5,'rigid_refinement':'L-BFGS-B 6D, rotations bounded +/-pi; translations +/-3A','reference_id':'B3','algorithm':'RDKit O3A initial alignment; B3-seeded training-only consensus; family-wise one-to-one Gaussian feature assignment; bounded rigid optimization'}
PARAMS['rigid_max_iterations']=300

def features(m,cid):
    raw=list(FACTORY.GetFeaturesForMol(m,confId=cid))
    lumps=[set(f.GetAtomIds()) for f in raw if f.GetFamily()=='LumpedHydrophobe']
    result=[]
    for f in raw:
        fam=f.GetFamily()
        if fam not in ['Donor','Acceptor','Aromatic','Hydrophobe','LumpedHydrophobe']: continue
        if fam=='Hydrophobe' and any(set(f.GetAtomIds()) <= s for s in lumps):continue
        if fam=='LumpedHydrophobe':fam='Hydrophobe'
        pos=f.GetPos()
        result.append({'family':fam,'atom_ids':list(f.GetAtomIds()),'xyz':np.array([pos.x,pos.y,pos.z])})
    return result

def make_ensemble(row,seed):
    m=Chem.MolFromSmiles(row['smiles']); assert m is not None
    opts=StereoEnumerationOptions(onlyUnassigned=True,unique=True,maxIsomers=8)
    isomers=list(EnumerateStereoisomers(m,options=opts))
    ensembles=[]
    for iso_idx,iso in enumerate(isomers):
        mh=Chem.AddHs(iso)
        ps=AllChem.ETKDGv3(); ps.randomSeed=seed+iso_idx; ps.pruneRmsThresh=PARAMS['prune_rms_A']; ps.numThreads=1;ps.useRandomCoords=False
        ids=list(AllChem.EmbedMultipleConfs(mh,numConfs=PARAMS['conformers_requested_per_stereoisomer'],params=ps))
        if not ids:raise RuntimeError('ETKDG failed '+row['id'])
        ff=AllChem.MMFFOptimizeMoleculeConfs(mh,numThreads=1,maxIters=PARAMS['mmff_max_iterations'],mmffVariant=PARAMS['mmff_variant'])
        energies={c:{'status':int(res[0]),'energy':float(res[1])} for c,res in zip(ids,ff)}
        minimum=min(e['energy'] for e in energies.values() if e['status']==0)
        keep=[c for c in ids if energies[c]['status']==0 and energies[c]['energy']-minimum<=PARAMS['energy_window_kcal_mol']]
        ensembles.append((mh,keep,energies,Chem.MolToSmiles(iso,isomericSmiles=True)))
    return ensembles

def initial_align(m,cid,ref,refid):
    o=AllChem.GetO3A(m,ref,AllChem.MMFFGetMoleculeProperties(m),AllChem.MMFFGetMoleculeProperties(ref),prbCid=cid,refCid=refid)
    rms=o.Align()
    return float(o.Score()),float(rms)

def assign(anchors,ff,cutoff=None):
    matches=[]
    for fam in COLORS:
        aa=[i for i,a in enumerate(anchors) if a['family']==fam]
        bb=[j for j,b in enumerate(ff) if b['family']==fam]
        if not aa or not bb:continue
        ds=np.linalg.norm(np.array([anchors[i]['xyz'] for i in aa])[:,None,:]-np.array([ff[j]['xyz'] for j in bb])[None,:,:],axis=2)
        if cutoff is None:
            sig=np.array([anchors[i]['radius_A'] for i in aa])[:,None]
            sim=np.exp(-ds**2/(2*sig**2))
            weights=np.array([anchors[i]['support_fraction'] for i in aa])[:,None]
            ai,bi=linear_sum_assignment(-sim*weights)
        else:ai,bi=linear_sum_assignment(ds)
        for i,j in zip(ai,bi):
            if cutoff is None or ds[i,j]<=cutoff:matches.append((aa[i],bb[j],float(ds[i,j])))
    return matches

def fit(anchors,ff):
    denom=sum(a['support_fraction'] for a in anchors)
    return sum(anchors[i]['support_fraction']*math.exp(-d*d/(2*anchors[i]['radius_A']**2)) for i,j,d in assign(anchors,ff))/denom

def json_feature(f):return {**f,'xyz':np.asarray(f['xyz']).round(6).tolist()}

def calculate():
    start=time.time();rows=list(csv.DictReader((P/'ligands.tsv').open(),delimiter='\t'))
    for r in rows:
        r['responsive']=int(r['responsive'])
        for k in ['ec50_uM','ec50_uncertainty_uM']:r[k]=float(r[k]) if r[k] else None
    ensembles={};counts={}
    for n,r in enumerate(rows):
        en=make_ensemble(r,PARAMS['seed']+n*100)
        ensembles[r['id']]=en
        counts[r['id']]={'stereoisomers':len(en),'generated':sum(m.GetNumConformers() for m,cs,ee,sm in en),'retained':sum(len(cs) for m,cs,ee,sm in en),'convergence_failures':sum(sum(v['status']!=0 for v in ee.values()) for m,cs,ee,sm in en)}
        print('Conformers',r['id'],counts[r['id']],flush=True)
    ref,cs,ee,sm=ensembles[PARAMS['reference_id']][0]
    refid=min(cs,key=lambda c:ee[c]['energy'])
    training=[]
    for r in rows:
        if r['split']!='training':continue
        candidates=[]
        for m,cs,ee,sm in ensembles[r['id']]:
            for c in cs:
                score,rms=initial_align(m,c,ref,refid)
                candidates.append((score,-ee[c]['energy'],m,c,sm))
        _,_,m,c,sm=max(candidates,key=lambda x:x[:2])
        training.append((r,m,c,features(m,c)))
    anchors=features(ref,refid)
    # A reference-seeded consensus is an explicit model choice, not a discovered receptor pocket.
    # Five iterations yield calculated centroid positions, with one vote per training ligand/site.
    for iteration in range(5):
        groups={i:[] for i in range(len(anchors))}
        for r,m,c,ff in training:
            for i,j,d in assign(anchors,ff,PARAMS['training_matching_cutoff_A']):groups[i].append((r['id'],ff[j]['xyz']))
        for i,a in enumerate(anchors):
            if groups[i]:a['xyz']=np.mean([x[1] for x in groups[i]],axis=0)
    model=[]
    for i,a in enumerate(anchors):
        grp=groups[i]; frac=len(grp)/len(training)
        if frac<PARAMS['minimum_training_support']:continue
        xyz=np.array([x[1] for x in grp]);rms=float(np.sqrt(np.mean(np.sum((xyz-a['xyz'])**2,axis=1))))
        model.append({'id':f'{a["family"]}_{sum(b["family"]==a["family"] for b in model)+1}','family':a['family'],'xyz':a['xyz'],'radius_A':max(PARAMS['radius_floor_A'],PARAMS['radius_dispersion_multiplier']*rms),'rms_dispersion_A':rms,'support_fraction':frac,'support_n':len(grp),'training_ids':[x[0] for x in grp]})
    assert any(a['family']=='Donor' for a in model), 'Model has no donor support'
    assert any(a['family']=='Acceptor' for a in model)
    print('Consensus',[(a['id'],a['support_n'],round(a['radius_A'],3)) for a in model],flush=True)
    results=[];sdf=Chem.SDWriter(str(OUT/'aligned_ranked.sdf'))
    rigid_stats={'attempted':0,'successful':0,'not_converged':0,'messages':{}}
    records=[]
    for r in rows:
        best=None
        for m,cs,ee,sm in ensembles[r['id']]:
            for cid in cs:
                initial_align(m,cid,ref,refid)
                ff=features(m,cid); xyz=np.array([f['xyz'] for f in ff])
                def transformed(p):
                    rot=Rotation.from_rotvec(p[:3]).as_matrix()
                    coords=xyz@rot.T+p[3:]
                    return [{**f,'xyz':v} for f,v in zip(ff,coords)]
                opt=minimize(lambda p:-fit(model,transformed(p)),np.zeros(6),method='L-BFGS-B',bounds=[(-math.pi,math.pi)]*3+[(-3.,3.)]*3,options={'maxiter':PARAMS['rigid_max_iterations'],'ftol':1e-10})
                rigid_stats['attempted']+=1
                rigid_stats['successful' if opt.success else 'not_converged']+=1
                msg=str(opt.message);rigid_stats['messages'][msg]=rigid_stats['messages'].get(msg,0)+1
                p=opt.x;score=fit(model,transformed(p))
                choice=(score,-ee[cid]['energy'])
                if best is None or choice>best[0]:
                    copy=Chem.Mol(m); conf=copy.GetConformer(cid)
                    atomxyz=np.array(conf.GetPositions())@Rotation.from_rotvec(p[:3]).as_matrix().T+p[3:]
                    for atomid,vec in enumerate(atomxyz):conf.SetAtomPosition(atomid,vec.tolist())
                    best=(choice,copy,cid,sm,ee[cid],transformed(p),opt.success,str(opt.message))
        choice,m,cid,sm,energy,ff,success,opt_message=best
        match=assign(model,ff)
        d={**r,'fit_score':round(choice[0],8),'selected_smiles':sm,'selected_conformer_id':cid,'mmff_energy_kcal_mol':energy['energy'],'mmff_status':energy['status'],'feature_counts':{fam:sum(f['family']==fam for f in ff) for fam in COLORS},'matched_features':[{'model_feature':model[i]['id'],'molecule_feature_index':j,'distance_A':round(dist,6)} for i,j,dist in match],'conformers':counts[r['id']],'atoms': [{'element':a.GetSymbol(),'xyz':list(m.GetConformer(cid).GetAtomPosition(a.GetIdx()))} for a in m.GetAtoms()],'bonds':[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble(),'aromatic':b.GetIsAromatic()} for b in m.GetBonds()],'features':[json_feature(f) for f in ff],'molblock':Chem.MolToMolBlock(m,confId=cid),'mw_Da':Descriptors.MolWt(m),'tpsa_A2':rdMolDescriptors.CalcTPSA(m)}
        for k,v in {'_Name':r['id']+' '+r['name'],'fit_score':d['fit_score'],'responsive':r['responsive'],'split':r['split'],'ec50_uM':r['ec50_uM'] if r['ec50_uM'] is not None else 'not supplied'}.items():m.SetProp(k,str(v))
        d['selected_rigid_optimizer_success']=bool(success);d['selected_rigid_optimizer_message']=opt_message
        results.append(d);records.append((m,cid,d))
        print('Score',r['id'],round(d['fit_score'],4),'assay',r['responsive'],flush=True)
    results.sort(key=lambda r:r['fit_score'],reverse=True)
    for rank,r in enumerate(results,1):r['overall_rank']=rank
    holdout=sorted([r for r in results if r['split']=='holdout'],key=lambda x:x['fit_score'],reverse=True)
    for rank,r in enumerate(holdout,1):r['holdout_rank']=rank
    recmap={d['id']:(m,cid) for m,cid,d in records}
    for r in results:m,cid=recmap[r['id']];sdf.write(m,confId=cid)
    sdf.close()
    pos=[r['fit_score'] for r in holdout if r['responsive']==1];neg=[r['fit_score'] for r in holdout if r['responsive']==0]
    auc=float(np.mean([float(p>n)+.5*float(p==n) for p in pos for n in neg]))
    rho,pvalue=spearmanr([r['fit_score'] for r in holdout if r['responsive']],[ -math.log10(r['ec50_uM']*1e-6) for r in holdout if r['responsive']])
    metric={'holdout_positive_n':len(pos),'holdout_negative_n':len(neg),'ROC_AUC':auc,'top5_holdout_active_n':sum(r['responsive'] for r in holdout[:5]),'top10_holdout_active_n':sum(r['responsive'] for r in holdout[:10]),'positive_only_score_vs_pEC50_Spearman_rho':float(rho),'positive_only_score_vs_pEC50_Spearman_p':float(pvalue),'baseline_active_fraction':len(pos)/len(holdout),'caveat':'These 25 candidates were preselected by the original multi-stage pipeline; this is a small retrospective, biased holdout, not a prospective validation or potency model.'}
    rng=np.random.default_rng(730019);boot=[]
    for _ in range(5000):
        pp=rng.choice(pos,len(pos),replace=True);nn=rng.choice(neg,len(neg),replace=True)
        pair=pp[:,None]-nn[None,:];boot.append(float(np.mean((pair>0)+.5*(pair==0))))
    metric['ROC_AUC_stratified_bootstrap95_percentile_CI']=np.quantile(boot,[.025,.975]).tolist()
    metric['bootstrap_replicates']=5000;metric['bootstrap_seed']=730019
    payload={'title':'Olfr73 calculated ligand pharmacophore reconstruction','parameters':PARAMS,'consensus_features':[json_feature(a) for a in model],'training_n':len(training),'metrics':metric,'molecules':results,'sources':{'paper':'https://www.nature.com/articles/s42003-019-0384-8','supplement':'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs42003-019-0384-8/MediaObjects/42003_2019_384_MOESM2_ESM.pdf'},'limitations':['Ligand-only reconstruction; original receptor coordinates, Phase model and QSAR coefficients unavailable publicly.','No receptor docking, MD, exclusion volume, electrostatic field or quantum electron density is calculated.','Spheres are donor/acceptor, hydrophobic and aromatic feature tolerance regions; positions and dispersion are calculated from training ligand conformers.','Original assays are mouse Olfr73 cellular activation, not human perception.','Fit score measures geometry/chemistry resemblance; it is not EC50, probability of activation or predicted odor.','Training B ligands have known activity but their table contains no EC50; assays for held-out A ligands never enter score calculation.','A11 E/Z unspecified: both stereoisomers are enumerated and best geometric fit retained, making its score an optimistic bound.']}
    payload['rigid_optimization']=rigid_stats
    (OUT/'results.json').write_text(json.dumps(payload,indent=2,allow_nan=False))
    (OUT/'results.js').write_text('window.OLFR73_DATA = '+json.dumps(payload,allow_nan=False)+';\n')
    fields=['overall_rank','holdout_rank','id','name','split','responsive','fit_score','ec50_uM','ec50_uncertainty_uM','selected_smiles','selected_conformer_id','mmff_energy_kcal_mol','mmff_status','mw_Da','tpsa_A2']
    with (OUT/'ranked_candidates.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(results)
    (OUT/'pharmacophore.json').write_text(json.dumps([json_feature(a) for a in model],indent=2))
    manifest={'run_completed_UTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'elapsed_seconds':time.time()-start,'python':sys.version,'platform':platform.platform(),'rdkit':rdBase.rdkitVersion,'numpy':np.__version__,'scipy':scipy.__version__,'parameters':PARAMS,'conformers':counts,'rigid_optimization':rigid_stats,'selected_rigid_not_converged_n':sum(not r['selected_rigid_optimizer_success'] for r in results),'metrics':metric,'sha256':{str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [P/'ligands.tsv',P/'run_model.py',P/'sources'/'MOESM2.pdf',P/'structure_audit.json',P/'vendor'/'3Dmol-min.js'] if f.exists()}}
    manifest['rdkit_feature_definition_sha256']=hashlib.sha256((pathlib.Path(RDConfig.RDDataDir)/'BaseFeatures.fdef').read_bytes()).hexdigest()
    (OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2))
    render_figures(payload)
    print('METRICS',json.dumps(metric),flush=True)
    print('Finished seconds',round(time.time()-start,1),flush=True)

def render_mol(ax,r,color=None,feature_spheres=None,title=None):
    xyz=np.array([a['xyz'] for a in r['atoms']])
    for b in r['bonds']:
        if r['atoms'][b['a']]['element']=='H' or r['atoms'][b['b']]['element']=='H':continue
        v=xyz[[b['a'],b['b']]];ax.plot(v[:,0],v[:,1],v[:,2],color=color or '#64748b',lw=2.5,alpha=.9)
    for elem,col,size in [('C',color or '#334155',36),('O','#ef4444',65),('N','#2563eb',65),('S','#ca8a04',75),('Cl','#22c55e',75)]:
        sel=[i for i,a in enumerate(r['atoms']) if a['element']==elem]
        if sel:v=xyz[sel];ax.scatter(v[:,0],v[:,1],v[:,2],c=col,s=size,depthshade=True)
    if feature_spheres:
        u=np.linspace(0,2*np.pi,32);v=np.linspace(0,np.pi,20)
        for f in feature_spheres:
            q=f['xyz'];rad=f['radius_A'];xx=q[0]+rad*np.outer(np.cos(u),np.sin(v));yy=q[1]+rad*np.outer(np.sin(u),np.sin(v));zz=q[2]+rad*np.outer(np.ones_like(u),np.cos(v))
            ax.plot_surface(xx,yy,zz,color=COLORS[f['family']],alpha=.14,linewidth=0,shade=False)
    ax.set_xlabel('x / Å',fontsize=9);ax.set_ylabel('y / Å',fontsize=9);ax.set_zlabel('z / Å',fontsize=9)
    ax.tick_params(labelsize=8);ax.view_init(elev=27,azim=-65)
    if hasattr(render_mol,'bounds'):
        lo,hi=render_mol.bounds;ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_zlim(lo[2],hi[2]);ax.set_box_aspect(hi-lo)
    ax.set_proj_type('ortho')
    if title:ax.set_title(title,fontsize=10,pad=12)

def render_figures(d):
    holdout=sorted([r for r in d['molecules'] if r['split']=='holdout'],key=lambda x:x['fit_score'],reverse=True)
    model=d['consensus_features'];ref=next(r for r in d['molecules'] if r['id']=='B3')
    points=np.array([a['xyz'] for r in holdout[:5]+[ref] for a in r['atoms'] if a['element']!='H']+[ (np.array(f['xyz'])+sign*f['radius_A']).tolist() for f in model for sign in [-1,1]])
    render_mol.bounds=(points.min(0)-.7,points.max(0)+.7)
    # Display reference coordinates before model-specific refinement by using the best-fit exported reference;
    # it differs only by a rigid transformation and is rendered in the shared consensus coordinate frame.
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.titleweight':'bold'})
    fig=plt.figure(figsize=(16,11),facecolor='white');fig.suptitle('Mouse Olfr73 | Calculated 3D pharmacophore reconstruction',fontsize=18,fontweight='bold',y=.97)
    ax=fig.add_subplot(2,3,1,projection='3d');render_mol(ax,ref,feature_spheres=model,title='a  Isoeugenol + consensus feature tolerances')
    ax=fig.add_subplot(2,3,2,projection='3d')
    palette=['#475569','#06b6d4','#8b5cf6','#ea580c','#db2777']
    for i,r in enumerate(holdout[:5]):render_mol(ax,r,palette[i])
    render_mol(ax,{'atoms':[],'bonds':[]},feature_spheres=model,title='b  Top five held-out candidates, calculated overlay')
    ax=fig.add_subplot(2,3,3)
    top=holdout[:10];yy=np.arange(len(top));cols=['#10b981' if r['responsive'] else '#ef4444' for r in top]
    ax.barh(yy,[r['fit_score'] for r in top],color=cols);ax.set_yticks(yy,[r['id'] for r in top]);ax.invert_yaxis();ax.set_xlim(0,1);ax.set_xlabel('Computed feature-fit score');ax.set_title('c  Holdout ranking (green = active; red = no response)',fontsize=10)
    for i,r in enumerate(holdout[:3]):
        ax=fig.add_subplot(2,3,4+i,projection='3d');assay=f"EC50 {r['ec50_uM']:g} µM" if r['responsive'] else 'No active response'
        render_mol(ax,r,feature_spheres=model,title=f"{chr(100+i)}  #{i+1} {r['id']} | fit {r['fit_score']:.3f} | {assay}")
    handles=[Line2D([0],[0],marker='o',linestyle='',color=c,label=fam) for fam,c in COLORS.items()]
    fig.legend(handles=handles,loc='lower center',ncol=4,bbox_to_anchor=(.5,.045),frameon=False)
    fig.text(.5,.019,f"ETKDGv3 → MMFF94s → O3A → training consensus → feature screening. 25 training ligands; 25 held out. AUC = {d['metrics']['ROC_AUC']:.3f}.\nSpheres represent feature tolerance regions, not electron density. Ligand-only reconstruction; no receptor model or potency prediction.",ha='center',fontsize=10)
    fig.subplots_adjust(top=.90,bottom=.12,wspace=.28,hspace=.22);fig.savefig(OUT/'pharmacophore_panel.png',dpi=220);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(15,4.6));thresholds=sorted(set([r['fit_score'] for r in holdout]),reverse=True);tpr=[0];fpr=[0]
    for t in thresholds:tpr.append(sum(r['responsive']==1 and r['fit_score']>=t for r in holdout)/17);fpr.append(sum(r['responsive']==0 and r['fit_score']>=t for r in holdout)/8)
    axes[0].plot(fpr,tpr,marker='o',label=f"Holdout AUC {d['metrics']['ROC_AUC']:.3f}");axes[0].plot([0,1],[0,1],'--',color='#94a3b8');axes[0].set(xlabel='False positive rate',ylabel='True positive rate',title='Retrospective holdout ROC');axes[0].legend()
    rng=np.random.default_rng(73)
    for label,col,idx in [('No response','#ef4444',0),('Active','#10b981',1)]:
        rr=[r for r in holdout if r['responsive']==idx];axes[1].scatter(idx+rng.uniform(-.10,.10,len(rr)),[r['fit_score'] for r in rr],c=col,label=label)
    axes[1].set(xticks=[0,1],xticklabels=['No response (8)','Active (17)'],ylabel='Feature-fit score',title='All held-out compounds')
    rr=[r for r in holdout if r['responsive']];axes[2].scatter([r['fit_score'] for r in rr],[-np.log10(r['ec50_uM']*1e-6) for r in rr],color='#2563eb')
    offsets={'A4':(-23,12),'A5':(-23,-14),'A8':(-15,13),'A11':(7,-5),'A12':(8,-16),'A7':(-25,1),'A10':(-25,-12),'A9':(-26,2),'A3':(8,2),'A2':(7,5),'A13':(-26,-15),'A16':(5,-3),'A1':(-21,7),'A15':(-23,-1),'A14':(6,5),'A6':(7,5),'A17':(7,5)}
    for r in rr:axes[2].annotate(r['id'],(r['fit_score'],-np.log10(r['ec50_uM']*1e-6)),fontsize=8,xytext=offsets[r['id']],textcoords='offset points')
    axes[2].set_xlim(.27,1.07);axes[2].set_ylim(3.05,5.15)
    axes[2].set(xlabel='Feature-fit score',ylabel='Measured pEC50 (M)',title=f"Active-only potency association, ρ={d['metrics']['positive_only_score_vs_pEC50_Spearman_rho']:.2f}")
    fig.suptitle('Assays withheld from calculation | small, preselected candidate set',fontweight='bold');fig.tight_layout();fig.savefig(OUT/'holdout_validation.png',dpi=180);plt.close(fig)

if __name__=='__main__':calculate()
