from langdetect import detect, DetectorFactory, LangDetectException

# Ensure consistent results
DetectorFactory.seed = 0

questions = [
    "Қазақстан жер көлемі жөнінен дүние жүзінде nechinshi orynda?",
    "Қазақстан жер көлемі жөнінен дүние жүзінде тоғызыншы орында.",
    "What is the position of Kazakhstan in terms of land area globally?"
]

for q in questions:
    try:
        lang = detect(q)
        print(f"Question: {q}\nDetected Language: {lang}\n")
    except LangDetectException as e:
        print(f"Question: {q}\nError: {str(e)}\n")
