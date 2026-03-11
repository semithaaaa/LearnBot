import os
os.environ["GIT_PYTHON_REFRESH"] = "quiet"
import json
import time
import pandas as pd
import torch
import evaluate
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from google import genai
import spacy
import pytextrank
import matplotlib.pyplot as plt
import seaborn as sns

# Import local modules
from quiz_generation import QuizGenerator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DATASET_PATH = 'd:/Client 1/output/text_data.csv' # Output directory
OUTPUT_DIR = 'd:/Client 1/output'
NUM_SAMPLES = 5  # Number of samples to evaluate to save time during benchmarking

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY environment variable not set. Voice agent evaluation will fail.")

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def load_summarization_models():
    print("Loading Multi-Model Summarization Pipeline...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    models = {}

    # 1. Preferred Production Model: BART Large
    try:
        print("  Loading facebook/bart-large-cnn (Abstractive)...")
        models['BART'] = {
            'tokenizer': AutoTokenizer.from_pretrained("facebook/bart-large-cnn"),
            'model': AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn", device_map="auto", dtype=torch.float32),
            "type": "abstractive"
        }
    except Exception as e:
        print(f"Warning: Failed to load BART. Error: {e}")

    # 2. Old Baseline: MT5 Small
    try:
        print("  Loading google/mt5-small (Abstractive Baseline)...")
        models['mT5'] = {
            'tokenizer': AutoTokenizer.from_pretrained("google/mt5-small"),
            'model': AutoModelForSeq2SeqLM.from_pretrained("google/mt5-small", device_map="auto", dtype=torch.float32),
            "type": "abstractive"
        }
    except Exception as e:
        print(f"Warning: Failed to load mT5. Error: {e}")

    # 3. Extractive Baseline: TextRank (using spaCy+pytextrank)
    print("  Loading TextRank (Extractive Baseline via PyTextRank)...")
    try:
        nlp = spacy.load("xx_ent_wiki_sm") # Multi-lingual lightweight model already present in environment
    except OSError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "spacy", "download", "xx_ent_wiki_sm"])
        nlp = spacy.load("xx_ent_wiki_sm")
    
    if "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer", first=True)
    if "textrank" not in nlp.pipe_names:
        nlp.add_pipe("textrank")
    models['TextRank'] = {
        'model': nlp,
        'type': 'extractive'
    }

    return models, device

def evaluate_summarization(df, models, device):
    print("\n--- Comparative Summarization Evaluation ---")
    rouge = evaluate.load("rouge")
    all_results = []
    
    predictions_per_model = {name: [] for name in models.keys()}
    references = []

    for index, row in df.iterrows():
        input_text = str(row['alltext'])
        reference_summary = str(row['summarytext'])
        references.append(reference_summary)
        
        orig_len = max(1, len(input_text.split()))

        for name, m in models.items():
            start_time = time.time()
            gen_summary = ""

            if m['type'] == 'abstractive':
                inputs = m['tokenizer']([input_text], max_length=1024, truncation=True, return_tensors="pt").to(device)
                with torch.no_grad():
                    if name == 'BART':
                        summary_ids = m['model'].generate(
                            inputs["input_ids"], max_length=800, min_length=250, num_beams=6, length_penalty=3.0, early_stopping=True, forced_bos_token_id=0
                        )
                    else:
                        summary_ids = m['model'].generate(
                            inputs["input_ids"], max_length=512, min_length=50, num_beams=4, length_penalty=2.0, early_stopping=True, no_repeat_ngram_size=3, repetition_penalty=1.5, forced_bos_token_id=0
                        )
                gen_summary = m['tokenizer'].decode(summary_ids[0], skip_special_tokens=True)
                if name == 'mT5':
                    import re
                    gen_summary = re.sub(r'<extra_id_\d+>', '', gen_summary).strip()
            else:
                # TextRank Execution
                doc = m['model'](input_text)
                tr_sents = [sent.text for sent in doc._.textrank.summary(limit_phrases=15, limit_sentences=5)]
                gen_summary = " ".join(tr_sents)

            latency = time.time() - start_time
            sum_len = len(gen_summary.split())
            compression_ratio = (1 - (sum_len / orig_len)) * 100

            predictions_per_model[name].append(gen_summary)

            all_results.append({
                "model": name,
                "id": index,
                "latency_seconds": round(latency, 4),
                "original_word_count": orig_len,
                "summary_word_count": sum_len,
                "compression_ratio_percent": round(compression_ratio, 2)
            })
            print(f"  [{name}] Sample {index+1}/{len(df)} processed in {latency:.2f}s")

    # Compute ROUGE per model
    print("\nComputing structural ROUGE metrics across models...")
    final_metrics = {}
    for name in models.keys():
        rouge_res = rouge.compute(predictions=predictions_per_model[name], references=references, use_stemmer=True)
        model_results = [r for r in all_results if r['model'] == name]
        avg_latency = sum(r['latency_seconds'] for r in model_results) / len(model_results)
        avg_compression = sum(r['compression_ratio_percent'] for r in model_results) / len(model_results)
        
        final_metrics[name] = {
            "rouge1": rouge_res["rouge1"],
            "rouge2": rouge_res["rouge2"],
            "rougeL": rouge_res["rougeL"],
            "rougeLsum": rouge_res["rougeLsum"],
            "avg_latency_seconds": round(avg_latency, 4),
            "avg_compression_ratio": round(avg_compression, 2)
        }
        
    return final_metrics, all_results

def generate_comparative_plots(sum_metrics, sum_results):
    print("\nGenerating Matplotlib Visualizations...")
    sns.set_theme(style="whitegrid")
    
    # --- Plot 1: ROUGE Score Comparison ---
    models = list(sum_metrics.keys())
    rouge1 = [sum_metrics[m]['rouge1'] for m in models]
    rouge2 = [sum_metrics[m]['rouge2'] for m in models]
    rougeL = [sum_metrics[m]['rougeL'] for m in models]
    
    x = range(len(models))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar([i - width for i in x], rouge1, width, label='ROUGE-1', color='#4F46E5')
    ax.bar(x, rouge2, width, label='ROUGE-2', color='#10B981')
    ax.bar([i + width for i in x], rougeL, width, label='ROUGE-L', color='#F59E0B')
    
    ax.set_ylabel('Scores (0.0 to 1.0)')
    ax.set_title('Comparative ROUGE Metrics')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'eval_plot_rouge_comparison.png'), dpi=300)
    plt.close()

    # --- Plot 2: Latency Distribution (Boxplot) ---
    df_res = pd.DataFrame(sum_results)
    plt.figure(figsize=(8, 6))
    sns.boxplot(data=df_res, x='model', y='latency_seconds', hue='model', palette='Set2', legend=False)
    plt.title('Inference Latency by Model')
    plt.ylabel('Latency (Seconds)')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'eval_plot_latency_distribution.png'), dpi=300)
    plt.close()

    # --- Plot 3: Average Compression Ratio ---
    plt.figure(figsize=(8, 6))
    sns.barplot(data=df_res, x='model', y='compression_ratio_percent', hue='model', palette='pastel', legend=False)
    plt.title('Model Compression Ratio Outcomes')
    plt.ylabel('Compression Ratio (%)')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'eval_plot_compression_ratio.png'), dpi=300)
    plt.close()
    
    print("Plots strictly saved to output directory.")

from google.genai import types

def evaluate_voice_agent():
    print("\n--- Evaluating Gemini Voice Agent ---")
    results = []
    total_latency = 0
    
    test_prompts = [
        {"context": "Machine learning is a subset of AI.", "message": "What is machine learning?"},
        {"context": "Photosynthesis is how plants make food using sunlight.", "message": "Explain photosynthesis."},
        {"context": "The mitochondria is the powerhouse of the cell.", "message": "What does the mitochondria do?"}
    ]
    
    try:
        gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        for i, tp in enumerate(test_prompts):
            start_time = time.time()
            sys_instruct = f"You are a helpful AI tutor. You must answer the student's question strictly based on the following document context. Do not say you cannot read a PDF. If the answer is not in the context, say 'I cannot find that in the document.'\n\nHare is the document context:\n{tp['context']}"
            
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=tp['message'],
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruct,
                    temperature=0.3
                )
            )
            _ = response.text # Force resolution
            latency = time.time() - start_time
            
            total_latency += latency
            results.append({
                "test_id": i,
                "latency_seconds": round(latency, 4),
                "status": "success"
            })
            print(f"  Processed prompt {i+1}/{len(test_prompts)} in {latency:.2f}s")
    except Exception as e:
        print(f"  Gemini Evaluation Failed: {e}")
        results.append({
            "test_id": -1,
            "latency_seconds": 0,
            "status": f"failed: {e}"
        })
        
    metrics = {
        "avg_latency_seconds": round(total_latency / max(1, len(test_prompts)), 4)
    }
    return metrics, results

def evaluate_quiz_generation(df):
    print("\n--- Evaluating Quiz Generation ---")
    quiz_gen = QuizGenerator()
    results = []
    total_latency = total_mcqs = total_tf = total_fib = total_flash = 0
    
    for index, row in df.iterrows():
        input_text = str(row['alltext'])
        start_time = time.time()
        quiz_data = quiz_gen.process_text(input_text)
        latency = time.time() - start_time
        
        total_latency += latency
        mcq_count = len(quiz_data.get('mcqs', []))
        tf_count = len(quiz_data.get('true_false', []))
        fib_count = len(quiz_data.get('fill_in_the_blank', []))
        flash_count = len(quiz_data.get('flashcards', []))
        
        total_mcqs += mcq_count; total_tf += tf_count; total_fib += fib_count; total_flash += flash_count
        
        results.append({
            "id": index,
            "latency_seconds": round(latency, 4),
            "mcqs_generated": mcq_count,
            "true_false_generated": tf_count,
            "fill_in_blanks_generated": fib_count,
            "flashcards_generated": flash_count
        })
        print(f"  Processed sample {index+1}/{len(df)} in {latency:.2f}s (Yield: {mcq_count+tf_count+fib_count+flash_count} items)")
        
    metrics = {
        "avg_latency_seconds": round(total_latency / len(df), 4),
        "avg_mcqs_per_doc": round(total_mcqs / len(df), 2),
        "avg_true_false_per_doc": round(total_tf / len(df), 2),
        "avg_fill_in_blanks_per_doc": round(total_fib / len(df), 2),
        "avg_flashcards_per_doc": round(total_flash / len(df), 2)
    }
    return metrics, results

def main():
    ensure_output_dir()
    
    print(f"Loading dataset from {DATASET_PATH}...")
    try:
        df = pd.read_csv(DATASET_PATH).dropna(subset=['alltext', 'summarytext'])
        if len(df) > NUM_SAMPLES:
            df = df.sample(n=NUM_SAMPLES, random_state=42).reset_index(drop=True)
            print(f"Sampled {NUM_SAMPLES} documents for evaluation.")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    # 1. Evaluate Summarization across Multi-Models
    models, device = load_summarization_models()
    sum_metrics, sum_results = evaluate_summarization(df, models, device)
    
    # Generate Visualizations
    generate_comparative_plots(sum_metrics, sum_results)
    
    # 2. Evaluate Quizzes
    quiz_metrics, quiz_results = evaluate_quiz_generation(df)
    
    # 3. Evaluate Voice Agent
    voice_metrics, voice_results = evaluate_voice_agent()
    
    # Compile Final Report
    final_report = {
        "metadata": {
            "num_samples_evaluated": NUM_SAMPLES,
            "timestamp": time.time()
        },
        "model_performance": {
            "summarization": sum_metrics,
            "quiz_generation": quiz_metrics,
            "voice_agent": voice_metrics
        }
    }
    
    # Save Results to Output Directory
    print(f"\nSaving tabular results to {OUTPUT_DIR}...")
    with open(os.path.join(OUTPUT_DIR, 'evaluation_summary.json'), 'w') as f:
        json.dump(final_report, f, indent=4)
        
    pd.DataFrame(sum_results).to_csv(os.path.join(OUTPUT_DIR, 'eval_summarization_details.csv'), index=False)
    pd.DataFrame(quiz_results).to_csv(os.path.join(OUTPUT_DIR, 'eval_quiz_details.csv'), index=False)
    pd.DataFrame(voice_results).to_csv(os.path.join(OUTPUT_DIR, 'eval_voice_details.csv'), index=False)
    
    print("\n Multi-Model Benchmark Complete! Thesis artifacts generated.")

if __name__ == "__main__":
    main()
