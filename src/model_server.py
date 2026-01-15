import torch
from flask import Flask, request, jsonify
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline
)

MODEL_PATH = "./models/qwen-7b"

app = Flask(__name__)

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True
)

print("Configuring 4-bit quantization...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
    llm_int8_enable_fp32_cpu_offload=True,
)

print("Loading model (ONLY ONCE)...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_config,
    device_map="balanced",
    max_memory={
        0: "7GB",
        "cpu": "32GB",
    },
    trust_remote_code=True,
    low_cpu_mem_usage=True,
)
model.eval()

print("Model server is ready.")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "")
    max_new_tokens = data.get("max_new_tokens", 256)

    if not prompt:
        return jsonify({"error": "prompt is required"}), 400

    messages = [{"role": "user", "content": prompt}]

    input_ids = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=0.1,
            top_p=0.9,
            do_sample=True,
        )

    response = tokenizer.decode(
        output_ids[0][input_ids.shape[-1]:],
        skip_special_tokens=True
    )

    return jsonify({
        "response": response
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
