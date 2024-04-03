# Simple workload
Simple workload for demonstrating the GLACIATION project.  

The application loads a dataset from the `source bucket` into memory, sorts the rows in the dataset, and writes the sorted dataset to the `target bucket`.  
In the dataset folder, there is an example dataset `example.csv` from [Machinery Fault Dataset](https://www.kaggle.com/datasets/uysalserkan/fault-induction-motor-dataset).  
Sorting is done based on the first column. The file should not contain headers.

## Usage
The repository contains Helm Charts that allow running Jobs in Kubernetes.

```bash
helm install simple-workload <helm-chart>
  --set arguments.time=<duration of work, sec., 3600 by default>
  --set arguments.minioHost=<URL MinIO API, localhost:9000 by default>
  --set arguments.minioAccessKey=<your_access_key>
  --set arguments.minioSecretKey=<your_secret_key>
  --set arguments.sourceBucket=<Name of a source bucket, "source" by default>
  --set arguments.targetBucket=<Name of a target bucket, "target" by default>
  --set arguments.datasetName=<Name of a dataset file, "example.csv" by default>
```

**Example**:

```bash
helm repo add simple-workload-repo https://glaciation-heu.github.io/simple-workload/helm-charts/
helm repo update
helm search repo simple-workload
```

Minimum configuration
```bash
helm install simple-workload simple-workload-repo/simple-workload
  --set arguments.minioAccessKey=<your_access_key>
  --set arguments.minioSecretKey=<your_secret_key>
```

Maximum configuration
```bash
helm install simple-workload simple-workload-repo/simple-workload
  --set arguments.time=60
  --set arguments.minioHost=localhost:9000
  --set arguments.minioAccessKey=<your_access_key>
  --set arguments.minioSecretKey=<your_secret_key>
  --set arguments.sourceBucket=my_source_bucket
  --set arguments.targetBucket=my_target_bucket
  --set arguments.datasetName=my_dataset_name.csv
```


## Development
### Prerequisites
  - Python 3.10+ - look at detailed instructions below
  - [pipx](https://pipx.pypa.io/stable/)
  - [Poetry](https://python-poetry.org/docs/)
  - [Docker](https://docs.docker.com/get-docker/)
  - [Helm](https://helm.sh/en/docs/)
  - [Minikube](https://minikube.sigs.k8s.io/docs/start/)
  - [MinIO](https://min.io/docs/minio/kubernetes/upstream/)

### Installation and running
1. If you don't have `Python` installed run:
    <details>
    <h4><summary>Install Python 3.12 if it is not available in your package manager</summary></h4>

    These instructions are for Ubuntu 22.04 and may not work for other versions.

    Also, these instructions are about using Poetry with Pyenv-managed (non-system) Python.
    
    ### Step 1: Update and Install Dependencies
    Before we install pyenv, we need to update our package lists for upgrades and new package installations. We also need to install dependencies for pyenv. 

    Open your terminal and type:  
    ```bash
    sudo apt-get update
    sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils \
    tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
    ```

    ### Step 2: Install Pyenv
    We will clone pyenv from the official GitHub repository and add it to our system path.
    ```bash
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    exec "$SHELL"
    ```
    For additional information visit official [docs](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation)

    ### Step 3: Install Python 3.12
    Now that pyenv is installed, we can install different Python versions. To install Python 3.12, use the following command:
    ```bash
    pyenv install 3.12
    ```

    ### Step 4: Connect Poetry to it
    Do this in the template dir. Pycharm will automatically connect to it later
    ```bash
    poetry env use ~/.pyenv/versions/3.12.1/bin/python
    ```
    (change the version number accordingly to what is installed)

    Finally, verify that Poetry indeed is connected to the proper version:
    ```bash
    poetry enf info
    ```
    </details>  

2. If you don't have `Poetry` installed run:
```bash
pipx install poetry
```

3. Install dependencies:
```bash
poetry config virtualenvs.in-project true
poetry install --no-root --with dev,test
```

4. Install `pre-commit` hooks:
```bash
poetry run pre-commit install
```

5. Launch the project:
```bash
poetry run python main.py <time> <minio_host> <minio_access_key> <minio_secret_key> <source_bucket> <target_bucket> <dataset_name>
```

## Manual build and deployment on Minikube
1. Install [Minikube](https://minikube.sigs.k8s.io/docs/start/).
2. Install [MinIO](https://min.io/docs/minio/kubernetes/upstream/).
3. Start Minikube:
```bash
minikube start
```
4. Create minio-dev.yaml file contains the following Kubernetes resources:
```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: minio
  name: minio
  namespace: default
spec:
  containers:
  - name: minio
    image: quay.io/minio/minio:latest
    command:
    - /bin/bash
    - -c
    args: 
    - minio server /mnt/disk1/minio-data --console-address :9090
    volumeMounts:
    - mountPath: /mnt/disk1/minio-data
      name: localvolume
  nodeSelector:
    kubernetes.io/hostname: minikube
  volumes:
  - name: localvolume
    hostPath:
      path: /mnt/disk1/minio-data
      type: DirectoryOrCreate
```
5. Apply minio-dev.yaml:
```bash
kubectl apply -f minio-dev.yaml
```
6. Forward ports:
```bash
kubectl port-forward minio 9000:9000
kubectl port-forward minio 9090:9090
```
7. Open [UI MinIO](http://localhost:9090) (login is `minioadmin`, password is `minioadmin`) and:
- Create Access and secret keys on the page [Access Keys](http://localhost:9090/access-keys);
- Create Source and Target buckets on the page [Buckets](http://localhost:9090/buckets);
- Upload Dataset `dataset/example.csv` to Source bucket on the page [Source bucket](http://localhost:9090/browser/source).
8. Build a docker image:
```bash
docker build . -t simple-workload:latest
```
9. Upload the docker image to minikube:
```bash
minikube image load simple-workload:latest
```
10.  Deploy the job:
```bash
helm install simple-workload ./charts/simple-workload
  --version 0.1.0
  --set image.repository=simple-workload
  --set image.tag=latest
  --set arguments.time=60
  --set arguments.minioHost=localhost:9000
  --set arguments.minioAccessKey=<your_access_key>
  --set arguments.minioSecretKey=<your_secret_key>
```

## Release
To create a release, add a tag in GIT with the format a.a.a, where 'a' is an integer.
```bash
git tag 0.1.0
git push origin 0.1.0
```
The release version for branches, pull requests, and other tags will be generated based on the last tag of the form a.a.a.

## Helm Chart Versioning
The Helm chart version changed automatically when a new release is created. The version of the Helm chart is equal to the version of the release.

## GitHub Actions
[GitHub Actions](https://docs.github.com/en/actions) triggers testing and builds for each release.  

**Initial setup**  
Create the branch [gh-pages](https://pages.github.com/) and use it as a GitHub page.  

**After execution**    
- The index.yaml file containing the list of Helm Charts will be available at `https://glaciation-heu.github.io/simple-workload/helm-charts/index.yaml`.
- The Docker image will be available at `https://github.com/orgs/glaciation-heu/packages?repo_name=simple-workload`.

# Collaboration guidelines
HIRO uses and requires from its partners [GitFlow with Forks](https://hirodevops.notion.site/GitFlow-with-Forks-3b737784e4fc40eaa007f04aed49bb2e?pvs=4)

## License
[MIT](https://choosealicense.com/licenses/mit/)
