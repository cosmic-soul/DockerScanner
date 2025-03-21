
import unittest
from unittest.mock import patch, MagicMock
import platform
import docker
from docker_manager.core.service_manager import DockerServiceManager
from docker_manager.core.health_report import HealthReport

class TestDockerServiceManager(unittest.TestCase):
    def setUp(self):
        self.manager = DockerServiceManager(demo_mode=True)
    
    def test_system_detection(self):
        self.assertIn(self.manager.system, ['linux', 'darwin', 'windows'])
        
    def test_service_status_demo(self):
        success, output = self.manager.get_status()
        self.assertTrue(success)
        
    def test_container_list_demo(self):
        success, output = self.manager.list_containers()
        self.assertTrue(success)

class TestHealthReport(unittest.TestCase):
    def setUp(self):
        self.health_report = HealthReport(demo_mode=True)
    
    def test_report_generation(self):
        success = self.health_report.generate_report()
        self.assertTrue(success)
        
    def test_recommendations(self):
        self.health_report.generate_report()
        self.assertIn('recommendations', self.health_report.report_data)

if __name__ == '__main__':
    unittest.main()
