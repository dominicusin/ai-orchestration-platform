"""
Универсальный AI провайдер с поддержкой 100+ API
OpenAI-совместимый интерфейс для любого LLM провайдера
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import aiohttp

logger = logging.getLogger("orchestration.ai.providers")


@dataclass
class ProviderConfig:
    """Конфигурация провайдера"""
    name: str
    base_url: str
    api_key_env: str
    model: str
    supports_vision: bool = False
    max_context: int = 128000
    needs_auth_header: bool = True


# Список провайдеров (OpenAI-совместимые)
OPENAI_COMPATIBLE_PROVIDERS = {
    # Основные
    "openai": ProviderConfig("OpenAI", "https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o"),
    "anthropic": ProviderConfig("Anthropic", "https://api.anthropic.com/v1", "ANTHROPIC_API_KEY", "claude-3-5-sonnet-20241022", True),
    "google": ProviderConfig("Google", "https://generativelanguage.googleapis.com/v1", "GEMINI_API_KEY", "gemini-2.0-flash-exp", True),
    "mistral": ProviderConfig("Mistral", "https://api.mistral.ai/v1", "MISTRAL_API_KEY", "mistral-large-latest"),
    "codestral": ProviderConfig("Codestral", "https://api.mistral.ai/v1", "MISTRAL_API_KEY", "codestral-latest"),
    
    # Российские
    "yandex": ProviderConfig("Yandex", "https://llm.api.cloud.yandex.net/foundationModels/v1", "YANDEX_API_KEY", "yandexgpt"),
    "yandex_cloud": ProviderConfig("Yandex Cloud", "https://llm.api.cloud.yandex.net/foundationModels/v1", "YC_TOKEN", "yandexgpt"),
    "sber": ProviderConfig("Sber", "https://api.sbercloud.ru/v1", "SBER_API_KEY", "AMI.Chat"),
    "gigachat": ProviderConfig("GigaChat", "https://gigachat.devices.sberbank.ru/api/v1", "GIGACHAT_TOKEN", "GigaChat"),
    
    # Китайские
    "deepseek": ProviderConfig("DeepSeek", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY", "deepseek-chat"),
    "qwen": ProviderConfig("Qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1", "DASHSCOPE_API_KEY", "qwen-plus"),
    "aliyun": ProviderConfig("Alibaba", "https://dashscope.aliyuncs.com/compatible-mode/v1", "DASHSCOPE_API_KEY", "qwen-turbo"),
    "minimax": ProviderConfig("MiniMax", "https://api.minimax.chat/v1", "MINIMAX_API_KEY", "abab6.5s-chat"),
    "moonshot": ProviderConfig("Moonshot", "https://api.moonshot.cn/v1", "MOONSHOT_API_KEY", "moonshot-v1-8k"),
    "baidu": ProviderConfig("Baidu", "https://qianfan.baidubce.com/v2", "BAIDU_API_KEY", "ernie-4.0-8k"),
    "bytedance": ProviderConfig("ByteDance", "https://ark.cn-beijing.volces.com/api/v3", "BYTEVOLCENGINE_API_KEY", "doubao-pro-32k"),
    "tencent": ProviderConfig("Tencent", "https://hunyuan.cloud.tencent.com", "TENCENT_SECRET_ID", "hunyuan-pro-32k"),
    "zhipu": ProviderConfig("Zhipu", "https://open.bigmodel.cn/api/paas/v4", "ZHIPU_API_KEY", "glm-4-plus"),
    
    # Европейские
    "cerebras": ProviderConfig("Cerebras", "https://api.cerebras.ai/v1", "CEREBRAS_API_KEY", "llama-3.3-70b"),
    "hyperbolic": ProviderConfig("Hyperbolic", "https://api.hyperbolic.xyz/v1", "HYPERBOLIC_API_KEY", "meta-llama/Llama-3.3-70B-Instruct"),
    "cohere": ProviderConfig("Cohere", "https://api.cohere.ai/v1", "COHERE_API_KEY", "command-r-plus"),
    "together": ProviderConfig("Together AI", "https://api.together.xyz/v1", "TOGETHER_API_KEY", "meta-llama/Llama-3.3-70B-Instruct"),
    "fireworks": ProviderConfig("Fireworks", "https://api.fireworks.ai/inference/v1", "FIREWORKS_API_KEY", "accounts/fireworks/models/llama-v3-70b-instruct"),
    "replicate": ProviderConfig("Replicate", "https://api.replicate.com/v1", "REPLICATE_API_KEY", "meta-llama/llama-3-70b-instruct"),
    "predibase": ProviderConfig("Predibase", "https://serving.predibase.com/v1", "PREDIBASE_API_KEY", "llama-3-70b"),
    "friendli": ProviderConfig("Friendli", "https://api.friendli.ai/v1", "FRIENDLI_TOKEN", "meta-llama/Llama-3.3-70b-instruct"),
    "baseten": ProviderConfig("Baseten", "https://app.baseten.co/api/v1", "BASETEN_API_KEY", "llama-70b"),
    "deepinfra": ProviderConfig("Deep Infra", "https://api.deepinfra.com/v1", "DEEPINFRA_API_KEY", "meta-llama/Llama-3.3-70B-Instruct"),
    
    # Азиатские
    "nebius": ProviderConfig("Nebius", "https://api.nebius.ai/v1", "NEBIUS_API_KEY", "meta-llama/Llama-3.3-70B-Instruct"),
    "sakura": ProviderConfig("Sakura", "https://api.sakura.io/v1", "SAKURA_API_KEY", "llama-3-70b"),
    "lepton": ProviderConfig("Lepton", "https://api.lepton.ai/rest/v1", "LEPTON_API_KEY", "llama-3.1-70b"),
    "modal": ProviderConfig("Modal", "https://modal.chat/v1", "MODAL_TOKEN", "llama-3.1-70b"),
    "novita": ProviderConfig("Novita", "https://api.novita.ai/v3", "NOVITA_API_KEY", "meta-llama/llama-3.3-70b-instruct"),
    "upstage": ProviderConfig("Upstage", "https://api.upstage.ai/v1", "UPSTAGE_API_KEY", "solar-pro"),
    "kimi": ProviderConfig("Kimi", "https://api.moonshot.cn/v1", "MOONSHOT_API_KEY", "moonshot-v1-8k"),
    
    # Американские
    "groq": ProviderConfig("Groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY", "llama-3.3-70b-versatile"),
    "github": ProviderConfig("GitHub", "https://models.inference.ai.azure.com", "GITHUB_TOKEN", "gpt-4o"),
    "perplexity": ProviderConfig("Perplexity", "https://api.perplexity.ai", "PERPLEXITY_API_KEY", "llama-3.1-sonar-large-128k-online"),
    "xai": ProviderConfig("xAI", "https://api.x.ai/v1", "XAI_API_KEY", "grok-2-1212"),
    
    # Прокси/агрегаторы
    "openrouter": ProviderConfig("OpenRouter", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "anthropic/claude-3.5-sonnet"),
    "vercel": ProviderConfig("Vercel", "https://gateway.ai.vercel.sh", "VERCEL_AI_GATEWAY_TOKEN", "openai/gpt-4o"),
    "cloudflare": ProviderConfig("Cloudflare", "https://gateway.ai.cloudflare.com/v1/account/{account_id}/gateway", "CF_API_TOKEN", "@cf/meta/llama-3.1-70b-instruct"),
    "azure": ProviderConfig("Azure", "https://{resource}.openai.azure.com/openai/deployments/{deployment}", "AZURE_OPENAI_API_KEY", "gpt-4o"),
    "aws_bedrock": ProviderConfig("AWS Bedrock", "https://bedrock-runtime.{region}.amazonaws.com", "AWS_ACCESS_KEY_ID", "anthropic.claude-3-sonnet"),
    
    # Локальные
    "ollama": ProviderConfig("Ollama", "http://localhost:11434", "OLLAMA_URL", "gemma3:1b", False, 8192),
    "lmstudio": ProviderConfig("LMStudio", "http://localhost:1234/v1", "LMSTUDIO_API_KEY", "local-model"),
    "localai": ProviderConfig("LocalAI", "http://localhost:8080/v1", "LOCALAI_API_KEY", "llama-3-70b"),
    "vllm": ProviderConfig("vLLM", "http://localhost:8000/v1", "VLLM_API_KEY", "llama-3-70b"),
    
    # Китайские прокси
    "siliconflow": ProviderConfig("SiliconFlow", "https://api.siliconflow.cn/v1", "SILICONFLOW_API_KEY", "Qwen/Qwen2-72B-Instruct"),
    "chutes": ProviderConfig("Chutes", "https://api.chutes.ai/v1", "CHUTES_API_KEY", "meta-llama/Meta-Llama-3.1-70B-Instruct"),
    
    # Другие
    "sambanova": ProviderConfig("SambaNova", "https://api.sambanova.ai/v1", "SAMBA_API_KEY", "Meta-Llama-3.1-70B-Instruct"),
    "giskard": ProviderConfig("Giskard", "https://api.giskard.ai/v1", "GISKARD_API_KEY", "llama-3-70b"),
    "runpod": ProviderConfig("RunPod", "https://api.runpod.ai/v2", "RUNPOD_API_KEY", "meta-llama-3.1-70b-instruct"),
    "scaleway": ProviderConfig("Scaleway", "https://api.scaleway.ai/v1", "SCW_SECRET_KEY", "llama-3-70b"),
    "ovh": ProviderConfig("OVHcloud", "https://endpoints.ai.cloud.ovh.net", "OVH_AI_ENDPOINTS_TOKEN", "Llama-3.70B"),
    "stacking": ProviderConfig("STACKIT", "https://ai-api.sapps.so", "STACKIT_API_KEY", "llama-3-70b"),
    "io_net": ProviderConfig("IO.NET", "https://io.net/v1", "IONET_API_KEY", "meta-llama/Llama-3.3-70B-Instruct"),
    "weights": ProviderConfig("Weights", "https://api.weights.ai/v1", "WEIGHTS_API_KEY", "llama-3-70b"),
    "vertex": ProviderConfig("Vertex", "https://{location}-aiplatform.googleapis.com/v1", "GOOGLE_APPLICATION_CREDENTIALS", "gemini-2.0-flash"),
    "nova": ProviderConfig("Nova", "https://nova.my", "NOVA_API_KEY", "nova-pro"),
    "abacus": ProviderConfig("Abacus", "https://api.abacus.ai", "ABACUS_API_KEY", "Smaug-72B"),
    "aihubmix": ProviderConfig("AIHubMix", "https://api.aihubmix.com/v1", "AIHUBMIX_KEY", "mixtral-8x7b"),
    "bailing": ProviderConfig("Bailing", "https://bailing-api.cn", "BAILING_KEY", "qwen-72b"),
    "berget": ProviderConfig("Berget", "https://api.berget.ai/v1", "BERGET_KEY", "llama-3-70b"),
    "clarifai": ProviderConfig("Clarifai", "https://api.clarifai.com/v2", "CLARIFAI_API_KEY", "meta-llama/llama-3-70b"),
    "cloudferro": ProviderConfig("CloudFerro", "https://sherlock.cloudferro.com/v1", "CLOUDFERRO_KEY", "llama-3-70b"),
    "cortecs": ProviderConfig("Cortecs", "https://cortecs.ai/v1", "CORTECS_KEY", "llama-3-70b"),
    "d_run": ProviderConfig("D.Run", "https://api.drun.chat/v1", "DRUN_KEY", "qwen-72b"),
    "evroc": ProviderConfig("evroc", "https://ai.evroc.com/v1", "EVROC_KEY", "llama-3-70b"),
    "fastrouter": ProviderConfig("FastRouter", "https://fastrouter.cloud/v1", "FASTROUTER_KEY", "llama-3-70b"),
    "firmware": ProviderConfig("Firmware", "https://firmware.ai/v1", "FIRMWARE_KEY", "llama-3-70b"),
    "inception": ProviderConfig("Inception", "https://api.inception.ai/v1", "INCEPTION_KEY", "llama-3-70b"),
    "jiekou": ProviderConfig("Jiekou", "https://api.jiekou.ai/v1", "JIEKOU_KEY", "qwen-72b"),
    "kilo": ProviderConfig("Kilo Gateway", "https://api.kilo.exchange/v1", "KILO_KEY", "llama-3-70b"),
    "lmstudio_cloud": ProviderConfig("LMStudio Cloud", "https://lmstudio.cloud/v1", "LMSTUDIO_CLOUD_KEY", "llama-3-70b"),
    "lucidquery": ProviderConfig("LucidQuery", "https://lucidquery.ai/v1", "LUCIDQUERY_KEY", "llama-3-70b"),
    "meganova": ProviderConfig("Meganova", "https://api.meganova.ai/v1", "MEGANOVA_KEY", "qwen-72b"),
    "moark": ProviderConfig("Moark", "https://api.moark.io/v1", "MOARK_KEY", "llama-3-70b"),
    "modelscope": ProviderConfig("ModelScope", "https://api.modelscope.cn/v1", "MODELSCOPE_API_KEY", "qwen-72b"),
    "morph": ProviderConfig("Morph", "https://api.morph.ai/v1", "MORPH_KEY", "llama-3-70b"),
    "nanogpt": ProviderConfig("NanoGPT", "https://api.nanogpt.io/v1", "NANOGPT_KEY", "llama-3-70b"),
    "nebius_token": ProviderConfig("Nebius Token", "https://token.nebius.ai/v1", "NEBIUS_TOKEN", "llama-3-70b"),
    "privatemode": ProviderConfig("Privatemode", "https://api.privatemode.ai/v1", "PRIVATEMODE_KEY", "llama-3-70b"),
    "qihang": ProviderConfig("QiHang", "https://api.qihang.ai/v1", "QIHANG_KEY", "qwen-72b"),
    "qiniu": ProviderConfig("Qiniu", "https://ai.qiniu.com/v1", "QINIU_ACCESS_KEY", "qwen-72b"),
    "requesty": ProviderConfig("Requesty", "https://api.requesty.ai/v1", "REQUESTY_KEY", "llama-3-70b"),
    "sap": ProviderConfig("SAP AI Core", "https://api.ai.core.sap/v1", "SAP_API_KEY", "llama-3-70b"),
    "siliconflow_cn": ProviderConfig("SiliconFlow CN", "https://api.siliconflow.cn/v1", "SF_CN_KEY", "qwen-plus"),
    "stepfun": ProviderConfig("StepFun", "https://api.stepfun.com/v1", "STEPFUN_KEY", "step-1-8k"),
    "submodel": ProviderConfig("submodel", "https://api.submodel.ai/v1", "SUBMODEL_KEY", "llama-3-70b"),
    "synthetic": ProviderConfig("Synthetic", "https://api.synthetic.ai/v1", "SYNTHETIC_KEY", "llama-3-70b"),
    "vivgrid": ProviderConfig("Vivgrid", "https://api.vivgrid.com/v1", "VIVGRID_KEY", "llama-3-70b"),
    "vultr": ProviderConfig("Vultr", "https://api.vultr.com/v1", "VULTR_API_KEY", "llama-3-70b"),
    "xiaomi": ProviderConfig("Xiaomi", "https://api.xiaomi.com/v1", "XIAOMI_KEY", "llama-3-70b"),
    "zenmux": ProviderConfig("ZenMux", "https://api.zenmux.com/v1", "ZENMUX_KEY", "llama-3-70b"),
    "zhipu_coding": ProviderConfig("Zhipu Coding", "https://open.bigmodel.cn/api/paas/v4", "ZHIPU_CODING_KEY", "glm-4-coder"),
    "ai302": ProviderConfig("302.AI", "https://api.302.ai/v1", "AI302_KEY", "gpt-4o"),
    "codingplan": ProviderConfig("Coding Plan", "https://codingplan.cn/v1", "CODINGPLAN_KEY", "qwen-72b"),
    "kuae": ProviderConfig("KUAE", "https://kuae.cn/v1", "KUAE_KEY", "qwen-72b"),
}


class UniversalProvider:
    """Универсальный провайдер для OpenAI-совместимых API"""
    
    def __init__(self, name: str, config: ProviderConfig):
        self.name = name
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._available = self._check()
    
    def _check(self) -> bool:
        """Проверка доступности провайдера"""
        # Для Ollama особая проверка
        if self.name == "ollama":
            try:
                import urllib.request
                url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                with urllib.request.urlopen(f"{url}/api/tags", timeout=2) as r:
                    return r.status == 200
            except:
                return False
        
        api_key = os.getenv(self.config.api_key_env)
        return bool(api_key)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def complete(
        self, 
        prompt: str, 
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system_prompt: str = ""
    ) -> Optional[str]:
        """Вызов LLM"""
        if not self._available:
            return None
        
        try:
            session = await self._get_session()
            
            # Ollama - особый случай
            if self.name == "ollama":
                url = f"{self.config.base_url}/api/generate"
                body = {
                    "model": self.config.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_ctx": min(self.config.max_context, 8192)},
                }
                async with session.post(
                    url, 
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("response", "")
                    logger.warning(f"[{self.name}] API error: {resp.status}")
                    return None
            
            # Для остальных провайдеров
            api_key = os.getenv(self.config.api_key_env)
            if not api_key:
                return None
            
            # Формирование URL
            url = f"{self.config.base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            
            # Особенности провайдеров
            if self.name == "anthropic":
                headers["x-api-key"] = api_key
                headers["anthropic-version"] = "2023-06-01"
                url = f"{self.config.base_url}/messages"
                body = {
                    "model": self.config.model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                }
            elif self.name == "ollama":
                body = {
                    "model": self.config.model,
                    "prompt": prompt,
                    "stream": False,
                }
            elif self.name == "google":
                url = f"{self.config.base_url}/models/{self.config.model}:generateContent"
                body = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens,
                    }
                }
            else:
                body = {
                    "model": self.config.model,
                    "messages": [
                        {"role": "system", "content": system_prompt} if system_prompt else {},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
            
            async with session.post(
                url, 
                json=body, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Парсинг ответа
                    if self.name == "ollama":
                        return data.get("response", "")
                    elif self.name == "google":
                        return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    elif self.name == "anthropic":
                        return data.get("content", [{}])[0].get("text", "")
                    else:
                        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                logger.warning(f"[{self.name}] API error: {resp.status}")
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"[{self.name}] Timeout")
            return None
        except Exception as e:
            logger.warning(f"[{self.name}] Error: {e}")
            return None
    
    async def close(self):
        if self._session:
            await self._session.close()


class ProviderManager:
    """Менеджер провайдеров"""
    
    def __init__(self):
        self.providers: Dict[str, UniversalProvider] = {}
        self._init_providers()
    
    def _init_providers(self):
        """Инициализация всех провайдеров"""
        for name, config in OPENAI_COMPATIBLE_PROVIDERS.items():
            provider = UniversalProvider(name, config)
            if provider._available:
                self.providers[name] = provider
                logger.info(f"   ✅ {config.name}")
    
    def get(self, name: str) -> Optional[UniversalProvider]:
        return self.providers.get(name)
    
    def list_available(self) -> List[str]:
        return list(self.providers.keys())
    
    async def close_all(self):
        for p in self.providers.values():
            await p.close()


# Глобальный менеджер
_manager: Optional[ProviderManager] = None


def get_provider_manager() -> ProviderManager:
    global _manager
    if _manager is None:
        _manager = ProviderManager()
    return _manager


def list_providers() -> List[str]:
    return get_provider_manager().list_available()
