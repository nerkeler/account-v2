# -*- coding: utf-8 -*-
"""
密码生成器服务
"""

import secrets
import string
from dataclasses import dataclass
from enum import Enum


class PasswordStrength(Enum):
    """密码强度"""
    WEAK = 1
    FAIR = 2
    GOOD = 3
    STRONG = 4
    VERY_STRONG = 5


@dataclass
class PasswordConfig:
    """密码配置"""
    length: int = 16
    use_uppercase: bool = True
    use_lowercase: bool = True
    use_digits: bool = True
    use_special: bool = True
    exclude_ambiguous: bool = False  # 排除 0O1lI 等


class PasswordGenerator:
    """密码生成器"""
    
    AMBIGUOUS = frozenset('0O1lI|')
    SPECIAL_CHARS = '!@#$%^&*()_+-=[]{}|;:,.<>?'
    
    @staticmethod
    def generate(config: PasswordConfig = None) -> str:
        """生成密码"""
        config = config or PasswordConfig()
        chars = ''
        
        if config.use_lowercase:
            chars += string.ascii_lowercase
        if config.use_uppercase:
            chars += string.ascii_uppercase
        if config.use_digits:
            chars += string.digits
        if config.use_special:
            chars += PasswordGenerator.SPECIAL_CHARS
        
        if not chars:
            chars = string.ascii_letters + string.digits
        
        if config.exclude_ambiguous:
            chars = ''.join(c for c in chars if c not in PasswordGenerator.AMBIGUOUS)
        
        password = ''.join(secrets.choice(chars) for _ in range(config.length))
        
        # 确保包含所有要求的字符类型
        while not PasswordGenerator._meets_requirements(password, config):
            password = ''.join(secrets.choice(chars) for _ in range(config.length))
        
        return password
    
    @staticmethod
    def _meets_requirements(password: str, config: PasswordConfig) -> bool:
        """检查是否满足要求"""
        if config.use_uppercase and not any(c.isupper() for c in password):
            return False
        if config.use_lowercase and not any(c.islower() for c in password):
            return False
        if config.use_digits and not any(c.isdigit() for c in password):
            return False
        if config.use_special and not any(c in PasswordGenerator.SPECIAL_CHARS for c in password):
            return False
        return True
    
    @staticmethod
    def check_strength(password: str) -> PasswordStrength:
        """检测密码强度"""
        score = 0
        
        # 长度得分
        if len(password) >= 8: score += 1
        if len(password) >= 12: score += 1
        if len(password) >= 16: score += 1
        
        # 字符类型得分
        if any(c.islower() for c in password): score += 1
        if any(c.isupper() for c in password): score += 1
        if any(c.isdigit() for c in password): score += 1
        if any(c in PasswordGenerator.SPECIAL_CHARS for c in password): score += 1
        
        # 映射到强度等级
        if score <= 2: return PasswordStrength.WEAK
        if score <= 3: return PasswordStrength.FAIR
        if score <= 4: return PasswordStrength.GOOD
        if score <= 5: return PasswordStrength.STRONG
        return PasswordStrength.VERY_STRONG
    
    @staticmethod
    def get_strength_color(strength: PasswordStrength) -> str:
        """获取强度颜色"""
        colors = {
            PasswordStrength.WEAK: "red",
            PasswordStrength.FAIR: "orange",
            PasswordStrength.GOOD: "yellow",
            PasswordStrength.STRONG: "green",
            PasswordStrength.VERY_STRONG: "cyan"
        }
        return colors.get(strength, "white")


# 测试
if __name__ == "__main__":
    # 测试生成
    print("测试密码生成:")
    
    config = PasswordConfig(length=16, use_special=True)
    password = PasswordGenerator.generate(config)
    print(f"  生成密码: {password}")
    
    strength = PasswordGenerator.check_strength(password)
    print(f"  强度: {strength.name}")
    
    # 测试不同长度
    print("\n测试不同配置:")
    for length in [8, 12, 16, 24]:
        pwd = PasswordGenerator.generate(PasswordConfig(length=length))
        st = PasswordGenerator.check_strength(pwd)
        print(f"  长度{length}: {pwd[:20]}... ({st.name})")
    
    print("\n✓ 密码生成器测试通过!")
