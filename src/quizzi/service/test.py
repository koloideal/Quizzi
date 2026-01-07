from dataclasses import dataclass
from datetime import datetime

from quizzi.domain.schemas import Test
from quizzi.infrastructure.database.dao.test import TestDAO
from quizzi.infrastructure.database.dao.user import UserDAO
from quizzi.infrastructure.database.repo.test import TestRepository
from quizzi.infrastructure.database.repo.test_attempt import TestAttemptRepository
from quizzi.infrastructure.utils.config import Config
from quizzi.infrastructure.utils.test_id_to_hash import decode_id, encode_id
from quizzi.infrastructure.utils.timezone import now_msk_naive


@dataclass
class TestValidationResult:
    is_valid: bool
    error: str = ""
    test: Test | None = None


@dataclass
class TestAccessResult:
    can_access: bool
    error: str = ""
    remaining_attempts: int | None = None


@dataclass
class TestUpdateResult:
    success: bool
    message: str


class TestService:
    def __init__(
        self,
        test_dao: TestDAO,
        test_repo: TestRepository,
        attempt_repo: TestAttemptRepository,
        user_dao: UserDAO,
        config: Config,
    ) -> None:
        self._test_dao = test_dao
        self._test_repo = test_repo
        self._attempt_repo = attempt_repo
        self._user_dao = user_dao
        self._config = config
    
    def decode_test_hash(self, test_hash: str) -> int | None:
        try:
            return decode_id(test_hash, self._config.security.encode_key)
        except (ValueError, IndexError):
            return None
    
    def encode_test_id(self, test_id: int) -> str:
        return encode_id(
            test_id,
            self._config.security.encode_key,
            self._config.security.encoded_string_length,
        )
    
    async def validate_test(self, test_id: int, user_id: int) -> TestValidationResult:
        test = await self._test_dao.get_by_id(test_id)
        
        if not test:
            return TestValidationResult(is_valid=False, error="❌ Тест не найден")
        
        if not test.is_active:
            return TestValidationResult(is_valid=False, error="❌ Тест деактивирован", test=test)
        
        if test.expires_at and test.expires_at < now_msk_naive():
            return TestValidationResult(is_valid=False, error="❌ Срок действия теста истек", test=test)
        
        user = await self._user_dao.get_by_id(user_id)
        if test.for_group and user and user.group != test.for_group:
            return TestValidationResult(
                is_valid=False,
                error=f"❌ Тест доступен только для группы {test.for_group}",
                test=test,
            )
        
        return TestValidationResult(is_valid=True, test=test)
    
    async def check_test_access(self, test_id: int, user_id: int) -> TestAccessResult:
        test = await self._test_dao.get_by_id(test_id)
        
        if not test:
            return TestAccessResult(can_access=False, error="❌ Тест не найден")
        
        if not test.is_active:
            return TestAccessResult(can_access=False, error="❌ Тест деактивирован")
        
        if test.expires_at and test.expires_at < now_msk_naive():
            return TestAccessResult(can_access=False, error="❌ Срок действия теста истек")
        
        if test.attempts:
            attempts = await self._attempt_repo.get_user_test_attempts(user_id, test_id)
            finished_attempts = [a for a in attempts if a.finished_at]
            remaining = test.attempts - len(finished_attempts)
            
            if remaining <= 0:
                return TestAccessResult(
                    can_access=False,
                    error="❌ Вы исчерпали все попытки",
                    remaining_attempts=0,
                )
            
            return TestAccessResult(can_access=True, remaining_attempts=remaining)
        
        return TestAccessResult(can_access=True)
    
    async def get_available_tests(self, user_id: int, user_group: int | None) -> list[Test]:
        return await self._test_repo.get_available_tests_for_user(user_id, user_group)
    
    async def toggle_test_active(self, test_id: int) -> TestUpdateResult:
        test = await self._test_dao.get_by_id(test_id)
        if not test:
            return TestUpdateResult(success=False, message="❌ Тест не найден")
        
        await self._test_dao.update(test_id, is_active=not test.is_active)
        action = "деактивирован" if test.is_active else "активирован"
        return TestUpdateResult(success=True, message=f"✅ Тест {action}")
    
    async def toggle_results_viewable(self, test_id: int) -> TestUpdateResult:
        test = await self._test_dao.get_by_id(test_id)
        if not test:
            return TestUpdateResult(success=False, message="❌ Тест не найден")
        
        await self._test_dao.update(test_id, are_results_viewable=not test.are_results_viewable)
        action = "скрыты" if test.are_results_viewable else "видны"
        return TestUpdateResult(success=True, message=f"✅ Результаты теперь {action}")
    
    async def delete_test(self, test_id: int) -> bool:
        return await self._test_dao.delete(test_id)
    
    async def update_password(self, test_id: int, password: str) -> TestUpdateResult:
        if len(password) > 255:
            return TestUpdateResult(success=False, message="❌ Пароль слишком длинный (максимум 255 символов)")
        await self._test_dao.update(test_id, password=password)
        return TestUpdateResult(success=True, message="✅ Пароль обновлен")
    
    async def remove_password(self, test_id: int) -> TestUpdateResult:
        await self._test_dao.update(test_id, password=None)
        return TestUpdateResult(success=True, message="✅ Пароль удален")
    
    async def update_attempts(self, test_id: int, attempts: int) -> TestUpdateResult:
        if attempts < 1:
            return TestUpdateResult(success=False, message="❌ Количество попыток должно быть больше 0")
        if attempts > 100:
            return TestUpdateResult(success=False, message="❌ Количество попыток не может быть больше 100")
        await self._test_dao.update(test_id, attempts=attempts)
        return TestUpdateResult(success=True, message="✅ Количество попыток обновлено")
    
    async def remove_attempts(self, test_id: int) -> TestUpdateResult:
        await self._test_dao.update(test_id, attempts=None)
        return TestUpdateResult(success=True, message="✅ Ограничение попыток удалено")
    
    async def update_time_limit(self, test_id: int, minutes: int) -> TestUpdateResult:
        if minutes < 1:
            return TestUpdateResult(success=False, message="❌ Лимит времени должен быть больше 0")
        if minutes > 1440:
            return TestUpdateResult(success=False, message="❌ Лимит времени не может быть больше 1440 минут (24 часа)")
        await self._test_dao.update(test_id, time_limit=minutes * 60)
        return TestUpdateResult(success=True, message="✅ Лимит времени обновлен")
    
    async def remove_time_limit(self, test_id: int) -> TestUpdateResult:
        await self._test_dao.update(test_id, time_limit=None)
        return TestUpdateResult(success=True, message="✅ Лимит времени удален")
    
    async def update_group(self, test_id: int, group: int) -> TestUpdateResult:
        await self._test_dao.update(test_id, for_group=group)
        return TestUpdateResult(success=True, message="✅ Группа обновлена")
    
    async def remove_group(self, test_id: int) -> TestUpdateResult:
        await self._test_dao.update(test_id, for_group=None)
        return TestUpdateResult(success=True, message="✅ Тест теперь доступен для всех групп")
    
    async def update_expires(self, test_id: int, expires_at: datetime) -> TestUpdateResult:
        await self._test_dao.update(test_id, expires_at=expires_at)
        return TestUpdateResult(success=True, message="✅ Срок действия обновлен")
    
    async def remove_expires(self, test_id: int) -> TestUpdateResult:
        await self._test_dao.update(test_id, expires_at=None)
        return TestUpdateResult(success=True, message="✅ Срок действия удален")
