"""
Kubernetes integration
Интеграция с Kubernetes
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum


class PodStatus(Enum):
    """Статус пода"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ServiceType(Enum):
    """Тип сервиса"""
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"


@dataclass
class Container:
    """Контейнер"""
    name: str
    image: str
    ports: list[int] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    resources: dict = field(default_factory=dict)
    command: list[str] = field(default_factory=list)


@dataclass
class Pod:
    """Под"""
    name: str
    namespace: str = "default"
    status: PodStatus = PodStatus.PENDING
    containers: list[Container] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)


@dataclass
class Service:
    """Сервис"""
    name: str
    namespace: str = "default"
    service_type: ServiceType = ServiceType.CLUSTER_IP
    selector: dict[str, str] = field(default_factory=dict)
    ports: list[dict] = field(default_factory=list)


@dataclass
class Deployment:
    """Deployment"""
    name: str
    namespace: str = "default"
    replicas: int = 1
    containers: list[Container] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)


class K8sClient:
    """Kubernetes клиент"""

    def __init__(self, config_path: str = None, in_cluster: bool = False):
        self.config_path = config_path
        self.in_cluster = in_cluster
        self._pods: dict[str, Pod] = {}
        self._services: dict[str, Service] = {}
        self._deployments: dict[str, Deployment] = {}

    async def create_pod(self, pod: Pod) -> bool:
        """Создание пода"""
        self._pods[pod.name] = pod
        return True

    async def get_pod(self, name: str, namespace: str = "default") -> Pod | None:
        """Получение пода"""
        return self._pods.get(name)

    async def delete_pod(self, name: str) -> bool:
        """Удаление пода"""
        if name in self._pods:
            del self._pods[name]
            return True
        return False

    async def list_pods(self, namespace: str = "default") -> list[Pod]:
        """Список подов"""
        return [p for p in self._pods.values() if p.namespace == namespace]

    async def create_service(self, service: Service) -> bool:
        """Создание сервиса"""
        self._services[service.name] = service
        return True

    async def get_service(self, name: str, namespace: str = "default") -> Service | None:
        """Получение сервиса"""
        return self._services.get(name)

    async def delete_service(self, name: str) -> bool:
        """Удаление сервиса"""
        if name in self._services:
            del self._services[name]
            return True
        return False

    async def list_services(self, namespace: str = "default") -> list[Service]:
        """Список сервисов"""
        return [s for s in self._services.values() if s.namespace == namespace]

    async def create_deployment(self, deployment: Deployment) -> bool:
        """Создание deployment"""
        self._deployments[deployment.name] = deployment
        return True

    async def get_deployment(self, name: str, namespace: str = "default") -> Deployment | None:
        """Получение deployment"""
        return self._deployments.get(name)

    async def scale_deployment(self, name: str, replicas: int) -> bool:
        """Масштабирование deployment"""
        if name in self._deployments:
            self._deployments[name].replicas = replicas
            return True
        return False

    async def delete_deployment(self, name: str) -> bool:
        """Удаление deployment"""
        if name in self._deployments:
            del self._deployments[name]
            return True
        return False

    async def list_deployments(self, namespace: str = "default") -> list[Deployment]:
        """Список deployments"""
        return [d for d in self._deployments.values() if d.namespace == namespace]


class K8sManifestGenerator:
    """Генератор манифестов Kubernetes"""

    @staticmethod
    def generate_pod_manifest(pod: Pod) -> dict:
        """Генерация манифеста пода"""
        containers = []
        for c in pod.containers:
            container = {
                "name": c.name,
                "image": c.image,
            }
            if c.ports:
                container["ports"] = [{"containerPort": p} for p in c.ports]
            if c.env:
                container["env"] = [{"name": k, "value": v} for k, v in c.env.items()]
            if c.command:
                container["command"] = c.command
            containers.append(container)

        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod.name,
                "namespace": pod.namespace,
                "labels": pod.labels,
                "annotations": pod.annotations,
            },
            "spec": {
                "containers": containers,
            },
        }
        return manifest

    @staticmethod
    def generate_deployment_manifest(deployment: Deployment) -> dict:
        """Генерация манифеста deployment"""
        containers = []
        for c in deployment.containers:
            container = {
                "name": c.name,
                "image": c.image,
            }
            if c.ports:
                container["ports"] = [{"containerPort": p} for p in c.ports]
            if c.env:
                container["env"] = [{"name": k, "value": v} for k, v in c.env.items()]
            containers.append(container)

        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": deployment.name,
                "namespace": deployment.namespace,
                "labels": deployment.labels,
            },
            "spec": {
                "replicas": deployment.replicas,
                "selector": {
                    "matchLabels": deployment.labels,
                },
                "template": {
                    "metadata": {
                        "labels": deployment.labels,
                    },
                    "spec": {
                        "containers": containers,
                    },
                },
            },
        }
        return manifest

    @staticmethod
    def generate_service_manifest(service: Service) -> dict:
        """Генерация манифеста сервиса"""
        ports = []
        for p in service.ports:
            port = {"port": p.get("port"), "targetPort": p.get("targetPort", p.get("port"))}
            if "name" in p:
                port["name"] = p["name"]
            ports.append(port)

        manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": service.name,
                "namespace": service.namespace,
            },
            "spec": {
                "type": service.service_type.value,
                "selector": service.selector,
                "ports": ports,
            },
        }
        return manifest


class K8sWatcher:
    """Наблюдатель за ресурсами K8s"""

    def __init__(self, client: K8sClient):
        self.client = client
        self._watchers: dict[str, asyncio.Task] = {}
        self._callbacks: dict[str, list[callable]] = {
            "pod": [],
            "service": [],
            "deployment": [],
        }

    def watch(self, resource_type: str, callback: callable):
        """Наблюдение за ресурсами"""
        if resource_type not in self._callbacks:
            self._callbacks[resource_type] = []
        self._callbacks[resource_type].append(callback)

    async def start_watching(self, resource_type: str):
        """Начало наблюдения"""
        if resource_type in self._watchers:
            return

        async def watch_loop():
            while True:
                await asyncio.sleep(5)
                # Simulate watching
                if resource_type == "pod":
                    pods = await self.client.list_pods()
                    for cb in self._callbacks.get("pod", []):
                        for pod in pods:
                            cb(pod)

        self._watchers[resource_type] = asyncio.create_task(watch_loop())

    async def stop_watching(self, resource_type: str):
        """Остановка наблюдения"""
        if resource_type in self._watchers:
            self._watchers[resource_type].cancel()
            del self._watchers[resource_type]


# Factory functions
def create_k8s_client(config_path: str = None) -> K8sClient:
    """Создание K8s клиента"""
    return K8sClient(config_path)


def create_container(name: str, image: str, ports: list[int] = None, env: dict = None) -> Container:
    """Создание контейнера"""
    return Container(
        name=name,
        image=image,
        ports=ports or [],
        env=env or {},
    )


def create_pod(name: str, containers: list[Container], labels: dict = None) -> Pod:
    """Создание пода"""
    return Pod(
        name=name,
        containers=containers,
        labels=labels or {},
    )


def create_deployment(name: str, containers: list[Container], replicas: int = 1, labels: dict = None) -> Deployment:
    """Создание deployment"""
    return Deployment(
        name=name,
        containers=containers,
        replicas=replicas,
        labels=labels or {},
    )


def create_service(name: str, selector: dict, ports: list[dict], service_type: ServiceType = ServiceType.CLUSTER_IP) -> Service:
    """Создание сервиса"""
    return Service(
        name=name,
        selector=selector,
        ports=ports,
        service_type=service_type,
    )
