from transformers import MarianMTModel, MarianTokenizer

class Translator:
    def __init__(self, model_name="Helsinki-NLP/opus-mt-fr-en"):
        self.tokenizer = MarianTokenizer.from_pretrained(model_name)
        self.model = MarianMTModel.from_pretrained(model_name)
        self.max_length = 512  

    def translate(self, text: str) -> str:
        sentences = text.split("\n")
        chunks, current_chunk = [], ""

        for sent in sentences:
            if len(self.tokenizer.encode(current_chunk + " " + sent)) < self.max_length:
                current_chunk += " " + sent
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sent
        if current_chunk:
            chunks.append(current_chunk.strip())

        translated = []
        for chunk in chunks:
            batch = self.tokenizer([chunk], return_tensors="pt", truncation=True, max_length=self.max_length)
            gen = self.model.generate(**batch)
            translated.append(self.tokenizer.decode(gen[0], skip_special_tokens=True))

        return " ".join(translated)

