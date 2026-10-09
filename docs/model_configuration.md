# Model Configuration

Model names and model families are centralized in `src/source_relocation/spec.py` and `configs/models/`. GPT-4o uses function calling via the OpenAI API. The same AgentDojo environment and registered tool definitions are reused across models. Open-weight adapters load Hugging Face checkpoints with deterministic generation, tokenization, and a shared external-task interface.

The RQ2 internal comparison uses Llama-3.1-8B-Instruct, Qwen2.5-7B-Instruct, DeepSeek-R1-Distill-Qwen-7B, Gemma-2-9B-IT, and Ministral-8B-Instruct-2410. Their decoder-layer counts are 32, 28, 28, 42, and 36, respectively.

Internal scores use a common neutral prediction prefix, `Promo code:`, and evaluate the complete target code by teacher forcing. The same model checkpoint must be used within each matched external and user-context unit.
