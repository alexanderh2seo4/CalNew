"""Model adapters are imported lazily so optional runtimes do not block curation."""


def make_model(config: dict, task: str, cache_root):
    family = config.get("family", "classical")
    if family == "classical":
        from .classical import ClassicalModel
        return ClassicalModel(config, task, cache_root)
    if family in ("graph", "mlp"):
        from .neural import NeuralModel
        return NeuralModel(config, task, cache_root)
    if family in ("molformer", "unimol2"):
        from .pretrained import PretrainedModel
        return PretrainedModel(config, task, cache_root)
    if family == "chemprop":
        from .external import ChempropModel
        return ChempropModel(config, task, cache_root)
    if family == "openpom":
        from .external import OpenPOMModel
        return OpenPOMModel(config, task, cache_root)
    if family == "receptor":
        raise ValueError('Receptor training requires molecular, sequence, assay and observed-pair data; use contextual.receptor_network')
    raise ValueError(f"Unknown model family: {family}")
