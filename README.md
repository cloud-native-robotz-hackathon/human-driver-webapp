# Robo Hackthon Demo / Test App

Simple web app show camera image boxes ;-)

![image](screenshot.png)

## Local development

```bash
# Build
podman build -t foo .   
# Run
podman run -ti --rm -p 5001:5000 -v $(pwd):/app:Z foo ./run.sh 
```