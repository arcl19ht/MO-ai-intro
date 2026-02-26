"""
测试SOPS加密的secrets文件
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from modules.YA_Secrets.secrets_parser import load_secrets, get_secret
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("test_secrets")


def test_secrets():
    """测试加密的secrets文件是否可正常读取"""
    try:
        # 测试加载所有secrets
        all_secrets = load_secrets()
        logger.info(f"成功加载secrets，包含密钥: {list(all_secrets.keys())}")

        # 测试获取DeepSeek API Key
        api_key = get_secret("deepseek_api_key")
        if api_key:
            # 只显示前6位和后4位，中间隐藏
            masked = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
            logger.info(f"DeepSeek API Key: {masked}")
            return True
        else:
            logger.error("未找到 deepseek_api_key")
            return False

    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False


if __name__ == "__main__":
    success = test_secrets()
    print(f"\n测试{'通过' if success else '失败'}")
