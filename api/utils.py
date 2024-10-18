# utils.py
import openai
import PyPDF2

# Установите ваш OpenAI API ключ
openai.api_key = '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'

# Функция для парсинга PDF
def parse_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ''
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()
    return text

# Генерация тестов с вариантами ответа
def generate_test_from_syllabus(syllabus_content, num_questions):
    prompt = (
        f"Create {num_questions} test questions in language based on the text with exactly 4 answer choices each based on the following syllabus:\n\n"
        f"{syllabus_content}\n\n"
        "Please provide the format strictly as follows:\n"
        "Вопрос: <question>\n"
        "A) <answer option 1>\n"
        "B) <answer option 2>\n"
        "C) <answer option 3>\n"
        "D) <answer option 4>\n"
        "Correct Answer: <correct letter>"
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
    )

    # Извлекаем текст ответа
    test_content = response['choices'][0]['message']['content']
    return test_content
