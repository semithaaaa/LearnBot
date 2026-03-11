import torch
import spacy
import random
import re
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class QuizGenerator:
    def __init__(self, model_name="facebook/bart-large-cnn"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            device_map="auto",
            dtype=torch.float32
        )
        
        try:
            self.nlp = spacy.load("xx_ent_wiki_sm")
        except OSError:
            import subprocess
            import sys
            subprocess.run([sys.executable, "-m", "spacy", "download", "xx_ent_wiki_sm"])
            self.nlp = spacy.load("xx_ent_wiki_sm")
            
        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer", first=True)

    def _generate_qg(self, context, answer):
        input_text = f"generate question: answer: {answer} context: {context} </s>"
        input_ids = self.tokenizer.encode(
            input_text, 
            return_tensors="pt", 
            max_length=512, 
            truncation=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids,
                max_length=64,
                num_beams=4,
                early_stopping=True,
                forced_bos_token_id=0
            )
            
        question = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        question = question.replace("question: ", "").replace("generate question: ", "").strip()
        return question

    def generate_mcqs(self, text, num_questions=7):
        doc = self.nlp(text)
        entities = list(set([ent.text for ent in doc.ents if len(ent.text) > 2]))
        
        if len(entities) < num_questions:
            words = [token.text for token in doc if not token.is_stop and token.is_alpha and len(token.text) > 3]
            entities.extend(list(set(words)))
            
        entities = list(set(entities))
        mcqs = []
        
        if not entities:
            return mcqs
            
        selected_entities = random.sample(entities, min(len(entities), num_questions))
        
        for answer in selected_entities:
            question = self._generate_qg(text, answer)
            distractors = [e for e in entities if e != answer]
            random.shuffle(distractors)
            distractors = distractors[:3]
            
            dummy_distractors = ["Option A", "Option B", "Option C", "Option D"]
            while len(distractors) < 3:
                distractors.append(dummy_distractors.pop())
                
            options = [answer] + distractors
            random.shuffle(options)
            
            mcqs.append({
                "question": question,
                "options": options,
                "answer": answer,
                "type": "mcq"
            })
        return mcqs

    def generate_true_false(self, text, num_questions=5):
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 30]
        
        tf_questions = []
        if not sentences:
            return tf_questions
            
        selected_sentences = random.sample(sentences, min(len(sentences), num_questions))
        
        for sent in selected_sentences:
            is_true = random.choice([True, False])
            
            if is_true:
                statement = sent
                answer = "True"
            else:
                words = sent.split()
                if len(words) > 3:
                    swap_idx = random.randint(1, len(words) - 2)
                    words[swap_idx] = "NOT"
                    statement = " ".join(words)
                else:
                    statement = f"It is false that {sent.lower()}"
                answer = "False"
                
            tf_questions.append({
                "question": statement,
                "options": ["True", "False"],
                "answer": answer,
                "type": "true_false"
            })
        return tf_questions

    def generate_fill_in_the_blank(self, text, num_questions=5):
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 20]
        
        fib_questions = []
        if not sentences:
            return fib_questions
            
        selected_sentences = random.sample(sentences, min(len(sentences), num_questions))
        
        for sent in selected_sentences:
            sent_doc = self.nlp(sent)
            keywords = [tok.text for tok in sent_doc if not tok.is_stop and tok.is_alpha and len(tok.text) > 4]
            
            if not keywords:
                continue
                
            blank_word = random.choice(keywords)
            pattern = re.compile(rf'\b{re.escape(blank_word)}\b', re.IGNORECASE)
            question_text = pattern.sub("_________", sent, count=1)
            
            fib_questions.append({
                "question": question_text,
                "options": [],
                "answer": blank_word,
                "type": "fill_in_the_blank"
            })
        return fib_questions

    def generate_flashcards(self, text, num_questions=15):
        doc = self.nlp(text)
        flashcards = []
        
        terms = list(set([ent.text for ent in doc.ents if len(ent.text) > 3]))
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 10]
        
        for term in terms[:num_questions]:
            for sent in sentences:
                if term in sent:
                    flashcards.append({
                        "term": term,
                        "definition": sent
                    })
                    break
                    
        return flashcards

    def process_text(self, text, num_mcq=7, num_tf=5, num_fib=5, num_flash=15):
        return {
            "mcqs": self.generate_mcqs(text, num_mcq),
            "true_false": self.generate_true_false(text, num_tf),
            "fill_in_the_blank": self.generate_fill_in_the_blank(text, num_fib),
            "flashcards": self.generate_flashcards(text, num_flash)
        }

if __name__ == "__main__":
    generator = QuizGenerator()
    sample_text = "Machine learning is a subset of artificial intelligence. It focuses on building systems that learn from data."
    print(generator.process_text(sample_text))
