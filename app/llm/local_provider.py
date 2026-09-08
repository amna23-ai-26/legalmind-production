from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


class LocalLLMProvider:
    def __init__(
        self,
        model_name,
        device="auto",
        max_new_tokens=512,
        temperature=0.2,
    ):
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map=device,
        )

        self.model.eval()

    def generate(self, prompt):
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
        )

        inputs = {
            key: value.to(self.model.device)
            for key, value in inputs.items()
        }

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=self.temperature > 0,
                temperature=self.temperature,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        generated = output[0][inputs["input_ids"].shape[1]:]

        return self.tokenizer.decode(
            generated,
            skip_special_tokens=True,
        ).strip()
