"""Tests for K8s Integration"""

import pytest
import asyncio

from orchestration.k8s_integration import (
    PodStatus,
    ServiceType,
    Container,
    Pod,
    Service,
    Deployment,
    K8sClient,
    K8sManifestGenerator,
    K8sWatcher,
    create_k8s_client,
    create_container,
    create_pod,
    create_deployment,
    create_service,
)


class TestContainer:
    """Test Container"""

    def test_creation(self):
        """Test creation"""
        c = Container(name="test", image="nginx:latest", ports=[80, 443])
        assert c.name == "test"
        assert c.image == "nginx:latest"
        assert 80 in c.ports


class TestPod:
    """Test Pod"""

    def test_creation(self):
        """Test creation"""
        container = Container(name="app", image="app:latest")
        pod = Pod(name="my-pod", containers=[container])
        assert pod.name == "my-pod"
        assert pod.status == PodStatus.PENDING


class TestService:
    """Test Service"""

    def test_creation(self):
        """Test creation"""
        service = Service(
            name="my-service",
            selector={"app": "myapp"},
            ports=[{"port": 80, "targetPort": 8080}],
        )
        assert service.name == "my-service"
        assert service.service_type == ServiceType.CLUSTER_IP


class TestDeployment:
    """Test Deployment"""

    def test_creation(self):
        """Test creation"""
        container = Container(name="app", image="app:latest")
        deployment = Deployment(name="my-deployment", containers=[container], replicas=3)
        assert deployment.name == "my-deployment"
        assert deployment.replicas == 3


class TestK8sClient:
    """Test K8sClient"""

    @pytest.fixture
    def client(self):
        """Create client"""
        return K8sClient()

    @pytest.mark.asyncio
    async def test_create_pod(self, client):
        """Test create pod"""
        container = Container(name="app", image="app:latest")
        pod = Pod(name="test-pod", containers=[container])
        result = await client.create_pod(pod)
        assert result is True
        assert await client.get_pod("test-pod") is not None

    @pytest.mark.asyncio
    async def test_delete_pod(self, client):
        """Test delete pod"""
        container = Container(name="app", image="app:latest")
        pod = Pod(name="test-pod", containers=[container])
        await client.create_pod(pod)
        result = await client.delete_pod("test-pod")
        assert result is True
        assert await client.get_pod("test-pod") is None

    @pytest.mark.asyncio
    async def test_list_pods(self, client):
        """Test list pods"""
        container = Container(name="app", image="app:latest")
        pod1 = Pod(name="pod1", containers=[container])
        pod2 = Pod(name="pod2", containers=[container])
        await client.create_pod(pod1)
        await client.create_pod(pod2)
        pods = await client.list_pods()
        assert len(pods) == 2

    @pytest.mark.asyncio
    async def test_create_service(self, client):
        """Test create service"""
        service = Service(name="my-service", selector={}, ports=[])
        result = await client.create_service(service)
        assert result is True

    @pytest.mark.asyncio
    async def test_scale_deployment(self, client):
        """Test scale deployment"""
        container = Container(name="app", image="app:latest")
        deployment = Deployment(name="my-deployment", containers=[container])
        await client.create_deployment(deployment)
        result = await client.scale_deployment("my-deployment", 5)
        assert result is True
        updated = await client.get_deployment("my-deployment")
        assert updated.replicas == 5


class TestK8sManifestGenerator:
    """Test K8sManifestGenerator"""

    def test_generate_pod_manifest(self):
        """Test generate pod manifest"""
        container = Container(name="app", image="app:latest", ports=[8080])
        pod = Pod(name="test-pod", containers=[container], labels={"app": "test"})
        manifest = K8sManifestGenerator.generate_pod_manifest(pod)
        assert manifest["kind"] == "Pod"
        assert manifest["metadata"]["name"] == "test-pod"
        assert manifest["spec"]["containers"][0]["image"] == "app:latest"

    def test_generate_deployment_manifest(self):
        """Test generate deployment manifest"""
        container = Container(name="app", image="app:latest")
        deployment = Deployment(name="test-deploy", containers=[container], replicas=3)
        manifest = K8sManifestGenerator.generate_deployment_manifest(deployment)
        assert manifest["kind"] == "Deployment"
        assert manifest["spec"]["replicas"] == 3

    def test_generate_service_manifest(self):
        """Test generate service manifest"""
        service = Service(
            name="test-service",
            selector={"app": "test"},
            ports=[{"port": 80, "targetPort": 8080}],
        )
        manifest = K8sManifestGenerator.generate_service_manifest(service)
        assert manifest["kind"] == "Service"
        assert manifest["spec"]["type"] == "ClusterIP"


class TestK8sWatcher:
    """Test K8sWatcher"""

    @pytest.fixture
    def watcher(self):
        """Create watcher"""
        client = K8sClient()
        return K8sWatcher(client)

    @pytest.mark.asyncio
    async def test_watch(self, watcher):
        """Test watch"""
        events = []

        def callback(pod):
            events.append(pod)

        watcher.watch("pod", callback)
        assert "pod" in watcher._callbacks


class TestFactoryFunctions:
    """Test factory functions"""

    def test_create_k8s_client(self):
        """Test create_k8s_client"""
        client = create_k8s_client()
        assert isinstance(client, K8sClient)

    def test_create_container(self):
        """Test create_container"""
        c = create_container("app", "app:latest", ports=[8080])
        assert c.name == "app"
        assert c.image == "app:latest"

    def test_create_pod(self):
        """Test create_pod"""
        c = create_container("app", "app:latest")
        pod = create_pod("test", [c])
        assert pod.name == "test"

    def test_create_deployment(self):
        """Test create_deployment"""
        c = create_container("app", "app:latest")
        d = create_deployment("test", [c], replicas=2)
        assert d.replicas == 2

    def test_create_service(self):
        """Test create_service"""
        s = create_service("test", {"app": "test"}, [{"port": 80}])
        assert s.name == "test"
