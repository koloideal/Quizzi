import json5
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParsedOption:
    text: str
    is_correct: bool


@dataclass
class ParsedQuestion:
    text: str
    question_type: str
    options: list[ParsedOption]
    correct_answer: str | None = None


@dataclass
class ParsedTest:
    title: str
    description: str | None
    password: str | None
    attempts: int | None
    expires_at: datetime | None
    for_group: int | None
    questions: list[ParsedQuestion]


@dataclass
class ParseError:
    message: str
    path: str | None = None


class TestParser:
    VALID_QUESTION_TYPES = {"single", "multiple", "input"}
    
    def parse(self, json_str: str) -> ParsedTest | list[ParseError]:
        try:
            data = json5.loads(json_str)
        except ValueError as e:
            return [ParseError(f"Невалидный JSON: {e}", path=None)]
        
        if not isinstance(data, dict):
            return [ParseError("JSON должен быть объектом", path=None)]
        
        errors: list[ParseError] = []
        
        title = self._parse_string(data, "title", required=True, max_length=255, errors=errors)
        description = self._parse_string(data, "description", required=False, max_length=2000, errors=errors)
        password = self._parse_string(data, "password", required=False, max_length=255, errors=errors)
        attempts = self._parse_int(data, "attempts", required=False, min_val=1, max_val=100, errors=errors)
        expires_at = self._parse_datetime(data, "expires_at", required=False, errors=errors)
        for_group = self._parse_int(data, "for_group", required=False, errors=errors)
        
        questions = self._parse_questions(data, errors)
        
        if errors:
            return errors
        
        assert title is not None
        
        return ParsedTest(
            title=title,
            description=description,
            password=password,
            attempts=attempts,
            expires_at=expires_at,
            for_group=for_group,
            questions=questions,
        )
    
    def _parse_string(
        self,
        data: dict,
        key: str,
        required: bool,
        max_length: int | None = None,
        errors: list[ParseError] | None = None,
    ) -> str | None:
        if errors is None:
            errors = []
        value = data.get(key)
        
        if value is None:
            if required:
                errors.append(ParseError(f"Поле '{key}' обязательно", path=key))
            return None
        
        if not isinstance(value, str):
            errors.append(ParseError(f"Поле '{key}' должно быть строкой", path=key))
            return None
        
        value = value.strip()
        if not value and required:
            errors.append(ParseError(f"Поле '{key}' не может быть пустым", path=key))
            return None
        
        if max_length and len(value) > max_length:
            errors.append(ParseError(f"Поле '{key}' слишком длинное (максимум {max_length})", path=key))
            return None
        
        return value if value else None
    
    def _parse_int(
        self,
        data: dict,
        key: str,
        required: bool,
        min_val: int | None = None,
        max_val: int | None = None,
        errors: list[ParseError] | None = None,
    ) -> int | None:
        if errors is None:
            errors = []
        value = data.get(key)
        
        if value is None:
            if required:
                errors.append(ParseError(f"Поле '{key}' обязательно", path=key))
            return None
        
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(ParseError(f"Поле '{key}' должно быть числом", path=key))
            return None
        
        if min_val is not None and value < min_val:
            errors.append(ParseError(f"Поле '{key}' должно быть не меньше {min_val}", path=key))
            return None
        
        if max_val is not None and value > max_val:
            errors.append(ParseError(f"Поле '{key}' должно быть не больше {max_val}", path=key))
            return None
        
        return value
    
    def _parse_datetime(
        self,
        data: dict,
        key: str,
        required: bool,
        errors: list[ParseError] | None = None,
    ) -> datetime | None:
        if errors is None:
            errors = []
        value = data.get(key)
        
        if value is None:
            if required:
                errors.append(ParseError(f"Поле '{key}' обязательно", path=key))
            return None
        
        if not isinstance(value, str):
            errors.append(ParseError(f"Поле '{key}' должно быть строкой в ISO формате", path=key))
            return None
        
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            errors.append(ParseError(f"Поле '{key}' должно быть в ISO формате (например 2026-12-31T23:59:59)", path=key))
            return None
    
    def _parse_questions(self, data: dict, errors: list[ParseError]) -> list[ParsedQuestion]:
        questions_data = data.get("questions")
        
        if questions_data is None:
            errors.append(ParseError("Поле 'questions' обязательно", path="questions"))
            return []
        
        if not isinstance(questions_data, list):
            errors.append(ParseError("Поле 'questions' должно быть массивом", path="questions"))
            return []
        
        if len(questions_data) == 0:
            errors.append(ParseError("Тест должен содержать хотя бы один вопрос", path="questions"))
            return []
        
        questions: list[ParsedQuestion] = []
        
        for i, q_data in enumerate(questions_data):
            path = f"questions[{i}]"
            
            if not isinstance(q_data, dict):
                errors.append(ParseError("Вопрос должен быть объектом", path=path))
                continue
            
            question = self._parse_question(q_data, path, errors)
            if question:
                questions.append(question)
        
        return questions
    
    def _parse_question(self, data: dict, path: str, errors: list[ParseError]) -> ParsedQuestion | None:
        text = data.get("question")
        if not text or not isinstance(text, str):
            errors.append(ParseError("Поле 'question' обязательно и должно быть строкой", path=f"{path}.question"))
            return None
        
        text = text.strip()
        if not text:
            errors.append(ParseError("Текст вопроса не может быть пустым", path=f"{path}.question"))
            return None
        
        if len(text) > 2000:
            errors.append(ParseError("Текст вопроса слишком длинный (максимум 2000)", path=f"{path}.question"))
            return None
        
        question_type = data.get("question_type")
        if not question_type or not isinstance(question_type, str):
            errors.append(ParseError("Поле 'question_type' обязательно", path=f"{path}.question_type"))
            return None
        
        if question_type not in self.VALID_QUESTION_TYPES:
            errors.append(ParseError(
                f"Неизвестный тип вопроса '{question_type}'. Допустимые: single, multiple, input",
                path=f"{path}.question_type"
            ))
            return None
        
        if question_type == "input":
            return self._parse_input_question(data, path, text, errors)
        else:
            return self._parse_choice_question(data, path, text, question_type, errors)
    
    def _parse_input_question(
        self,
        data: dict,
        path: str,
        text: str,
        errors: list[ParseError],
    ) -> ParsedQuestion | None:
        correct_answer = data.get("correct_answer")
        
        if not correct_answer or not isinstance(correct_answer, str):
            errors.append(ParseError(
                "Для типа 'input' поле 'correct_answer' обязательно",
                path=f"{path}.correct_answer"
            ))
            return None
        
        correct_answer = correct_answer.strip()
        if not correct_answer:
            errors.append(ParseError("Правильный ответ не может быть пустым", path=f"{path}.correct_answer"))
            return None
        
        if len(correct_answer) > 255:
            errors.append(ParseError("Правильный ответ слишком длинный (максимум 255)", path=f"{path}.correct_answer"))
            return None
        
        return ParsedQuestion(
            text=text,
            question_type="input",
            options=[ParsedOption(text=correct_answer, is_correct=True)],
            correct_answer=correct_answer,
        )
    
    def _parse_choice_question(
        self,
        data: dict,
        path: str,
        text: str,
        question_type: str,
        errors: list[ParseError],
    ) -> ParsedQuestion | None:
        options_data = data.get("answers")
        
        if not options_data or not isinstance(options_data, list):
            errors.append(ParseError(
                f"Для типа '{question_type}' поле 'answers' обязательно и должно быть массивом",
                path=f"{path}.answers"
            ))
            return None
        
        if len(options_data) < 2:
            errors.append(ParseError("Минимум 2 варианта ответа", path=f"{path}.answers"))
            return None
        
        if len(options_data) > 10:
            errors.append(ParseError("Максимум 10 вариантов ответа", path=f"{path}.answers"))
            return None
        
        options: list[ParsedOption] = []
        correct_count = 0
        
        for j, opt_data in enumerate(options_data):
            opt_path = f"{path}.answers[{j}]"
            
            if not isinstance(opt_data, dict):
                errors.append(ParseError("Вариант ответа должен быть объектом", path=opt_path))
                continue
            
            opt_text = opt_data.get("option")
            if not opt_text or not isinstance(opt_text, str):
                errors.append(ParseError("Поле 'option' обязательно", path=f"{opt_path}.option"))
                continue
            
            opt_text = opt_text.strip()
            if not opt_text:
                errors.append(ParseError("Текст варианта не может быть пустым", path=f"{opt_path}.option"))
                continue
            
            if len(opt_text) > 255:
                errors.append(ParseError("Текст варианта слишком длинный (максимум 255)", path=f"{opt_path}.option"))
                continue
            
            is_correct = opt_data.get("is_correct")
            if not isinstance(is_correct, bool):
                errors.append(ParseError("Поле 'is_correct' должно быть true или false", path=f"{opt_path}.is_correct"))
                continue
            
            if is_correct:
                correct_count += 1
            
            options.append(ParsedOption(text=opt_text, is_correct=is_correct))
        
        if len(options) < 2:
            return None
        
        if correct_count == 0:
            errors.append(ParseError("Должен быть хотя бы один правильный ответ", path=f"{path}.answers"))
            return None
        
        if question_type == "single" and correct_count > 1:
            errors.append(ParseError(
                f"Для типа 'single' должен быть ровно один правильный ответ (найдено {correct_count})",
                path=f"{path}.answers"
            ))
            return None
        
        return ParsedQuestion(
            text=text,
            question_type=question_type,
            options=options,
        )
