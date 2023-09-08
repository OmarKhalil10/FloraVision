# Create a new project

* Make sure that billing is enabled for your Google Cloud project.
* Enable the Artifact Registry, Cloud Build, and Google Kubernetes Engine APIs.
* Install the Google Cloud CLI.
* To initialize the gcloud CLI, run the following command:

```
gcloud init
```

* ```kubectl``` is used to manage Kubernetes, the cluster orchestration system used by GKE. You can install ```kubectl``` by using ```gcloud```:

```
gcloud components install kubectl
```


# Containerizing an app with Cloud Build

To containerize the sample app, create a new file named ```Dockerfile``` in the same directory as the source files, and copy the following content:

```
# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.7-slim

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
RUN pip install Flask gunicorn

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
```

## Add a ```.dockerignore``` file to ensure that local files don't affect the container build process:

```
Dockerfile
README.md
*.pyc
*.pyo
*.pyd
__pycache__
```

## Get your Google Cloud project ID:

```
gcloud config get-value project
```

## In this quickstart, you will store your container in Artifact Registry and deploy it to your cluster from the registry. Run the following command to create a repository named ```app-repo-gke``` in the same location as your cluster:

```
export PROJECT_ID=landmark-classifier
export LOCATION=europe-west6

```

```
gcloud artifacts repositories create app-repo-gke \
    --project=${PROJECT_ID} \
    --repository-format=docker \
    --location=${LOCATION} \
    --description="Docker repository"
```

## Build your container image using Cloud Build, which is similar to running ```docker build``` and ```docker push```, but the build happens on Google Cloud:

```
gcloud builds submit \
  --tag ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/app-repo-gke/flask-app-gke .
```

#### The image is stored in ```Artifact Registry```.

# Creating a GKE cluster

A GKE cluster is a managed set of Compute Engine virtual machines that operate as a single GKE cluster.

1. Create the cluster.

```
gcloud container clusters create-auto flask-app-gke \
  --location $LOCATION
```

2. Verify that you have access to the cluster. The following command lists the nodes in your container cluster which are up and running and indicates that you have access to the cluster.

```
kubectl get nodes
```

If you run into errors, refer to the [Kubernetes Troubleshooting guide](https://kubernetes.io/docs/tasks/debug/debug-cluster/).

# Deploying to GKE

To deploy your app to the GKE cluster you created, you need two Kubernetes objects.

1. A [Deployment](http://kubernetes.io/docs/concepts/workloads/controllers/deployment/) to define your app.
2. A [Service](https://kubernetes.io/docs/concepts/services-networking/service/) to define how to access your app.

## Deploy an app

The app has a frontend server that handles the web requests. You define the cluster resources needed to run the frontend in a new file called ```deployment.yaml```. These resources are described as a Deployment. You use Deployments to create and update a [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/) and its associated Pods.

1. Create the ```deployment.yaml``` file in the same directory as your other files and copy the following content. Replace the following values in your file:

```
$PROJECT_ID is your Google Cloud project ID:
$LOCATION is the repository location, such as europe-west6.

```

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-app-gke
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ml-gke
  template:
    metadata:
      labels:
        app: ml-gke
    spec:
      containers:
      - name: ml-gke-app
        # Replace $LOCATION with your Artifact Registry location (e.g., us-west1).
        # Replace $PROJECT_ID with your project ID.
        image: europe-west6-docker.pkg.dev/landmark-classifier/app-repo-gke/flask-app-gke:latest
        # This app listens on port 8080 for web traffic by default.
        ports:
        - containerPort: 8080
        env:
          - name: PORT
            value: "8080"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
            ephemeral-storage: "1Gi"
          limits:
            memory: "1Gi"
            cpu: "500m"
            ephemeral-storage: "1Gi"
```

2. Deploy the resource to the cluster:

```
kubectl apply -f deployment.yaml
```

3. Track the status of the Deployment:

```
kubectl get deployments
```

### The Deployment is complete when all of the ```AVAILABLE``` deployments are ```READY```.

```
NAME              READY   UP-TO-DATE   AVAILABLE   AGE
flask-app-gke    1/1     1            1           20s
```

#### If the Deployment has a mistake, run ```kubectl apply -f deployment.yaml``` again to update the Deployment with any changes.

4. After the Deployment is complete, you can see the Pods that the Deployment created:

```
kubectl get pods
```

# Deploy a Service

[Services](https://kubernetes.io/docs/concepts/services-networking/service/) provide a single point of access to a set of Pods. While it's possible to access a single Pod, Pods are ephemeral and can only be accessed reliably by using a service address. In your ml-gke-app, the "ml-gke" Service defines a [load balancer](https://kubernetes.io/docs/tasks/access-application-cluster/create-external-load-balancer/) to access the ```ml-gke-app``` Pods from a single IP address. This service is defined in the ```service.yaml``` file.

1. Create the file ```service.yaml``` in the same directory as your other source files with the following content:

```
# The ml-gke service provides a load-balancing proxy over the ml-gke-app
# pods. By specifying the type as a 'LoadBalancer', Kubernetes Engine will
# create an external HTTP load balancer.

apiVersion: v1
kind: Service
metadata:
  name: ml-gke
spec:
  type: LoadBalancer
  selector:
    app: ml-gke
  ports:
  - port: 80
    targetPort: 8080
```

The Pods are defined separately from the service that uses the Pods. Kubernetes uses [labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/) to select the pods that a service addresses. With labels, you can have a service that addresses Pods from different replica sets and have multiple services that point to an individual Pod.

2. Create the Hello World Service:

```
kubectl apply -f service.yaml
```

3. Get the external IP address of the service:

```
kubectl get services
```

It can take up to 60 seconds to allocate the IP address. The external IP address is listed under the column ```EXTERNAL-IP``` for the ml-gke Service.

```
NAME         TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE
ml-gke       LoadBalancer   10.22.222.222   35.111.111.11   80:32341/TCP   1m
kubernetes   ClusterIP      10.22.222.1     <none>          443/TCP        20m
```

# View a deployed app

You have now deployed all the resources needed to run the Hello ml-gke-app app on GKE.

Use the external IP address from the previous step to load the app in your web browser, and see your running app:

```
http://EXTERNAL_IP
```

Or, you can make a ```curl``` call to the external IP address of the service:

```
curl EXTERNAL_IP
```

The output displays the following:

```
Hello World!
```

# Deploying a new version of the sample app

In this section, you upgrade ```ml-gke-app``` to a new version by building and deploying a new Docker image to your GKE cluster.

GKE's [rolling update](https://cloud.google.com/kubernetes-engine/docs/how-to/updating-apps) feature lets you update your Deployments without downtime. During a rolling update, your GKE cluster incrementally replaces the existing ```ml-gke-app``` Pods with Pods containing the Docker image for the new version. During the update, your load balancer service routes traffic only into available Pods.


1. Return to Cloud Shell, where you have cloned the hello app source code and Dockerfile. Update the function hello_world() in the app.py file to report the new version 2.0.0.
2. Build and tag a new ```ml-gke-app``` Docker image ```new tag: v2``` 


# (Optional) 

1. Set the baseline number of Deployment ```replicas``` to 3.

```
kubectl scale deployment flask-app-gke --replicas=3
```

2. Create a ```HorizontalPodAutoscaler``` resource for your Deployment.

```
kubectl autoscale deployment flask-app-gke --cpu-percent=80 --min=1 --max=5
```

3. To see the Pods created, run the following command:

```
kubectl get pods
```

Output:

```
NAME                         READY   STATUS    RESTARTS   AGE
flask-app-gke-784d7569bc-hgmpx   1/1     Running   0          90s
flask-app-gke-784d7569bc-jfkz5   1/1     Running   0          90s
flask-app-gke-784d7569bc-mnrrl   1/1     Running   0          95s
```

#### Note Build your container image using Cloud Build, which is similar to running ```docker build``` and ```docker push```, but the build happens on Google Cloud:

```
gcloud builds submit \
  --tag ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/app-repo-gke/flask-app-gke:v2 .
```

Now you're ready to update your ```flask-app-gke``` Kubernetes Deployment to use a new Docker image.

### Note: Because you created a HorizontalPodAutoscaler earlier, the number of ```flask-app-gke``` Pods running in this section might be fewer than the three Pods initially deployed. Your GKE cluster might have scaled down the number of Pods based on low CPU usage.

1. Apply a rolling update to the existing ```flask-app-gke``` Deployment with an image update using the kubectl set image command:

```
kubectl set image deployment/flask-app-gke flask-app-gke=${LOCATION}-docker.pkg.dev/${PROJECT_ID}/app-repo-gke/flask-app-gke:v2
```

2. Watch the running Pods running the ```v1``` image stop, and new Pods running the ```v2``` image start.

```
watch kubectl get pods
```

```
NAME                        READY   STATUS    RESTARTS   AGE
flask-app-gke-89dc45f48-5bzqp   1/1     Running   0          2m42s
flask-app-gke-89dc45f48-scm66   1/1     Running   0          2m40s
```

3. In a separate tab, navigate again to the ml-gke-service External IP. You should now see the Version set to 2.0.0.

```
kubectl get services
```

# Clean up

To avoid incurring charges to your Google Cloud account for the resources used on this page, follow these steps.

You are charged for [the Compute Engine instances](https://cloud.google.com/kubernetes-engine/pricing) running in your cluster, as well as for [the container image in Artifact Registry](https://cloud.google.com/artifact-registry/pricing).

## Delete the project

Deleting your Google Cloud project stops billing for all the resources used within that project.

```
Caution: Deleting a project has the following effects:

- Everything in the project is deleted. If you used an existing project for the tasks in this document, when you delete it, you also delete any other work you've done in the project.

- Custom project IDs are lost. When you created this project, you might have created a custom project ID that you want to use in the future. To preserve the URLs that use the project ID, such as an appspot.com URL, delete selected resources inside the project instead of deleting the whole project.
```

1. In the Google Cloud console, go to the [Manage resources page](https://console.cloud.google.com/iam-admin/projects?_ga=2.152739385.1617127268.1693772630-1748766779.1689775824&_gac=1.121509242.1693413957.Cj0KCQjw0bunBhD9ARIsAAZl0E0rZeO4bX-ngLaIJahHiMi9x4i2otmMwOT0mmlSzOzZQN3JnG7Yna0aAmb2EALw_wcB).
2. In the project list, select the project that you want to delete, and then click **Delete**.
3. In the dialog, type the project ID, and then click **Shut down** to delete the project.

## Delete your cluster and container

If you want to keep your project but only delete the resources used in this tutorial, delete your cluster and image.

### To delete a cluster using the Google Cloud CLI, run the following command for the mode that you used:

```
gcloud container clusters delete flask-app-gke \
    --location ${LOCATION}
```

#### Note: For more information, refer to the documentation on [Deleting a cluster](https://cloud.google.com/kubernetes-engine/docs/how-to/deleting-a-cluster).

### To delete an image in your Artifact Registry repository, run the following command:

```
gcloud artifacts docker images delete \
    ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/app-repo-gke/flask-app-gke
```

#### Note: For more information, refer to the documentation on [Managing images](https://cloud.google.com/artifact-registry/docs/docker/manage-images#deleting_images).

### Delete the Service: This deallocates the Cloud Load Balancer created for your Service:

```
kubectl delete service <service_name>

```

### Delete the cluster: This deletes the resources that make up the cluster, such as the compute instances, disks, and network resources:

```
gcloud container clusters delete flask-app-gke --region europe-west6
```

### Delete your container images: This deletes the Docker images you pushed to Artifact Registry.

```
gcloud artifacts docker images delete \
    ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/app-repo-gke/flask-app-gke \
    --delete-tags --quiet
gcloud artifacts docker images delete \
    ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/app-repo-gke/flask-app-gke:v2 \
    --delete-tags --quiet
```

# What's next

For more information on Kubernetes, see the following:

* Learn more about [creating clusters](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-a-container-cluster).
* Learn more about [Kubernetes](http://kubernetes.io/).
* Read the ```kubectl``` [reference documentation](https://kubernetes.io/docs/reference/kubectl/).


### For more information on deploying to GKE, see the following:

* Learn how to [package, host, and deploy a simple web server application](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app).
* Cloud Code for [VS Code](https://cloud.google.com/code/docs/vscode/k8s-overview)