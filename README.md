# Capstone-RSD/rsd-yolov5-model

[![Linting and Unittest](https://github.com/Capstone-RSD/rsd-yolov5-model/actions/workflows/test_client.yml/badge.svg)](https://github.com/Capstone-RSD/rsd-yolov5-model/actions/workflows/test_client.yml)

Capstone-RSD/rsd-yolov5-model is a Python machine learning application that utilizes the YOLOv5 model for road surface deterioration detection, Apache Kafka for event streaming, and Neo4j for establishing relationships between the location of the damages and the damage captured. The application is designed to be deployed on Kubernetes and can be developed using Docker containers.

## Contents

The repository contains the following components:

- **YOLOv5 Model**: The core component of the application, the YOLOv5 model, is included in the repository. This model is trained to detect and classify various road damages.

- **devcontainer.json**: The repository includes a `devcontainer.json` file for development with docker containers. Can also be used in GitHub Codespaces.

- **Training Script**: The repository provides a Python [notebook](src/road1.ipynb) for training and generating the model for performing inferencing on new images using the trained YOLOv5 model. This script takes input images, performs its classification, and generates predictions with bounding boxes and class labels.

## Prequesities

The project relies on both Apache Kafka, Firebase Storage, Pytorch, and Neo4j. We recommend the following links on getting started with the following tools:

1. [Confluent - What is apache Kafka](https://www.confluent.io/what-is-apache-kafka/)
2. [Neo4j - Getting Started](https://neo4j.com/developer/get-started/)
3. [Generate Firebase Private key](https://youtu.be/MU7O6emzAc0) and download into the [src](/src/)
4. [Install PyTorch Locally](https://pytorch.org/get-started/locally/)

## Contribution

We welcome contributions to enhance the capabilities of the road surface detection and classification system. If you are interested in contributing, please follow these steps:

1. Fork the repository.
2. Create a new branch from the `main` branch for your changes.
3. Make your modifications, ensuring clear and concise commit messages.
4. Push your changes to your fork.
5. Create a pull request from your branch to the `dev` branch of this repository.

## Getting Started

To get started with the development of the road surface detection and classification system, follow these steps:

   1. Ensure the [prequesities](#prequesities) have been applied before proceeding

   2. Clone this repository:

        ```bash
        git clone https://github.com/Capstone-RSD/rsd-yolov5-model.git
        cd rsd-yolov5-model
        ```

   3. Install the required dependencies:

        ```bash
        pip install torch torchvision torchaudio # if pytorch isn't present see https://pytorch.org/get-started/locally/ for more details
        pip install -r requirements-dev.txt
        ```

   4. Run the application:

        ```bash
        python src/rss_consumer.py
                                    -b <host[:port]>        # Kafka Bootstrap server URL
                                    -t <topic_name>         # Kafka topic name
                                    -g <consumer_group>     # kafka Consumer group name
                                    --cluster_key <API_KEY>
                                    --cluster_secret <API_SECRET>
                                    --neo4j_db_username <db_username>
                                    --neo4j_db_password <db_password>
                                    --neo4j_db_uri <neo4j+s://...>
        ```

   5. Using an `.env` file:
       You can save some of these arguments as environment variables rather than passing them as arguments into the program

       ```sh
       CLUSTER_API_KEY=CLUSTER_API_KEY123
       CLUSTER_API_SECRET=CLUSTER_API_SECRET123
       NEO4J_DB_URI=neo4j+s://...
       NEO4J_DB_USERNAME=db_username
       NEO4J_DB_PASSWORD=db_password
       ```

Start developing and modifying the YOLOv5 model according to your requirements. **Note:** you may also use docker along with vscode devcontainers to setup your environment. See [Developing inside a Container](https://code.visualstudio.com/docs/devcontainers/containers) for more details.

## Deployment

To deploy the road surface detection and classification system on Kubernetes, follow the instructions below:

   1. Clone the repo into your GCP Cloud Editor and change your directory to the `rsd-yolov5-model` directory.

   2. Build the Docker image:

       ```sh
       docker build -t rsd-yolov5-model .
       ```

   3. Push the Docker image to a container registry of your choice.

   4. Deploy the application on Kubernetes using the provided deployment manifest.

       ```bash
       kubectl apply -f rsd-yolov5.yaml
       ```

Please note that you may need to update the deployment instructions and modify the provided [rsd-yolov5.yaml](rsd-yolov5.yaml) manifest to match your specific deployment requirements. This includes the application secrets and keys.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
