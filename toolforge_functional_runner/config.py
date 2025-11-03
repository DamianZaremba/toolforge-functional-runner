import dataclasses
import os
from base64 import b64decode
from pathlib import PosixPath

import paramiko


@dataclasses.dataclass(frozen=True)
class DeploymentRepo:
    url: str
    branch: str
    entrypoint: PosixPath


@dataclasses.dataclass(frozen=True)
class Prometheus:
    port: int


@dataclasses.dataclass(frozen=True)
class Target:
    host: str
    user: str
    ssh_fingerprints: list[paramiko.PKey]


@dataclasses.dataclass(frozen=True)
class Environment:
    tool: str
    project: PosixPath
    skip_suites: list[str]
    repo: PosixPath
    venv: PosixPath


@dataclasses.dataclass(frozen=True)
class Config:
    repo: DeploymentRepo = DeploymentRepo(
        url=os.environ.get(
            "TOOLFORGE_DEPLOY_URL",
            "https://gitlab.wikimedia.org/repos/cloud/toolforge/toolforge-deploy.git",
        ),
        branch=os.environ.get("TOOLFORGE_DEPLOY_BRANCH", "main"),
        entrypoint=PosixPath("functional-tests"),
    )
    monitoring: Prometheus = Prometheus(port=int(os.environ.get("PROMETHEUS_PORT", "9091")))
    target: Target = Target(
        host=os.environ.get("TARGET_HOST", "login.toolforge.org"),
        user=os.environ.get("TARGET_USER", "damian-scripts"),
        ssh_fingerprints=[
            paramiko.RSAKey(
                data=b64decode(
                    "AAAAB3NzaC1yc2EAAAADAQABAAABgQDXp2gEN/ZVXLEH7P3tykUnqVD5B+b7MqNizCMPNmVITpSdOeP61jo5HQzROijnrUUctuYnWdX5e/Igj5UZOL4N7ADOj6B2JxO2MensfNgHTdzhkomt0YvG0hD5UhpJEBzR2KaFuZoD1cs1aeo+da1OgxvM98V0QTEtHGeJ20U/UUj69VCK1crXQc8/CPbkXYvRDtnpTj2qwne8NmoGxNxFtAObmmRkDMiRlmO1MXclUa3a8bHzUv6dPu3belqf4Cz0rzUWFDR41F2jDU9py8otNY1mex/wv1z7v1jFIZXegON+k3bxlHCDuGipDJej2j9w5+ewdahZ2t/NjOjXdZFdbZHgCO79u4x+1EPHwJmpZtcRYJ3Ha2EOLWIFDyY0IfPEVNn0KZU/AEoQz0LlZP4DA2O3bgPus6RCVfvkgkyy7eIkKYmiYDvYXeDQWBDPtSHToPIpJu3ZKmDqY6F8RTTqHHdvNVd772FLnc/kJmA68FkvCgxXl4A3CXUAc1GbT8E="
                )
            ),
            paramiko.ECDSAKey(
                data=b64decode(
                    "AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBAkH+V1+iGMRLe9DnTn2hi/ibT723YRoBUYp3p0Eq52CNkzOyKSgdtF5+skyzPaOZU+ufH3M8GphQLbDhQCuVhY="
                )
            ),
            paramiko.Ed25519Key(data=b64decode("AAAAC3NzaC1lZDI1NTE5AAAAIHHCaBsit1GY3TeucMi3gDEIpQ8uNhokVa0dr/tM6PZa")),
        ],
    )
    environment: Environment = Environment(
        tool=os.environ.get("TARGET_TOOL", "test-damian"),
        skip_suites=["admin"],
        project=PosixPath(f'/data/project/{os.environ.get("TARGET_TOOL", "test-damian")}'),
        repo=PosixPath(f'/data/project/{os.environ.get("TARGET_TOOL", "test-damian")}/toolforge-deploy'),
        venv=PosixPath(f'/data/project/{os.environ.get("TARGET_TOOL", "test-damian")}/venv'),
    )
