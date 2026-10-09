from .spec import MODEL_IDS

OPEN_WEIGHT = ('llama31', 'qwen', 'gemma', 'mistral', 'deepseek')


def select_models(model=None, models=None, internal=False):
    allowed = OPEN_WEIGHT if internal else tuple(MODEL_IDS)
    requested = models if models is not None else (model or allowed[0])
    chosen = [item.strip() for item in requested.split(',')] if isinstance(requested, str) else list(requested)
    if chosen == ['all']:
        chosen = list(allowed)
    if not chosen or any(item not in allowed for item in chosen) or len(set(chosen)) != len(chosen):
        raise ValueError(f'Invalid model selection: {chosen}; allowed: {allowed}')
    return chosen
