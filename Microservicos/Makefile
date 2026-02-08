AWS_REGION      := us-east-1
ACCOUNT_ID      := 634510061385
REPO_NAME       := rag-microservices
IMAGE_TAG       := v10
IMAGE_URI       := $(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(REPO_NAME):$(IMAGE_TAG)
ROLE_ARN        := arn:aws:iam::634510061385:role/RodneySageMakerRole

ENDPOINT_NAME   := rag-microservices-endpoint
CONFIG_NAME     := rag-microservices-config
MODEL_NAME      := rag-microservices-model

deploy: clean build push create-model create-config create-endpoint

build:
	@echo "### [1/5] Buildando imagem v3..."
	docker build --no-cache -t $(REPO_NAME):$(IMAGE_TAG) .

push:
	@echo "### [2/5] Push para ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker tag $(REPO_NAME):$(IMAGE_TAG) $(IMAGE_URI)
	docker push $(IMAGE_URI)

create-model:
	-aws sagemaker delete-model --model-name $(MODEL_NAME)
	aws sagemaker create-model --model-name $(MODEL_NAME) --primary-container Image=$(IMAGE_URI) --execution-role-arn $(ROLE_ARN)

create-config:
	-aws sagemaker delete-endpoint-config --endpoint-config-name $(CONFIG_NAME)
	aws sagemaker create-endpoint-config --endpoint-config-name $(CONFIG_NAME) \
		--production-variants VariantName=AllTraffic,ModelName=$(MODEL_NAME),ServerlessConfig={MemorySizeInMB=6144,MaxConcurrency=1}

create-endpoint:
	-aws sagemaker delete-endpoint --endpoint-name $(ENDPOINT_NAME)
	aws sagemaker create-endpoint --endpoint-name $(ENDPOINT_NAME) --endpoint-config-name $(CONFIG_NAME)

status:
	@aws sagemaker describe-endpoint --endpoint-name $(ENDPOINT_NAME) --query "EndpointStatus" --output text

# No alvo test, vamos aumentar a paciência do comando AWS para 180s
test:
	@echo '{"query": "Qual a capital do Brasil?"}' > input.json
	@echo "### Invocando v4 (Aguardando carga dos modelos)..."
	aws sagemaker-runtime invoke-endpoint \
		--endpoint-name $(ENDPOINT_NAME) \
		--body fileb://input.json \
		--content-type application/json \
		--cli-read-timeout 180 \
		output.json
	@cat output.json

# Comando para monitorar o tempo de deploy com cronômetro
watch-deploy:
	@echo "### Iniciando cronômetro de deploy para a $(IMAGE_TAG)..."
	@start_time=$$(date +%s); \
	while true; do \
		status=$$(aws sagemaker describe-endpoint --endpoint-name $(ENDPOINT_NAME) --query "EndpointStatus" --output text 2>/dev/null); \
		current_time=$$(date +%s); \
		elapsed=$$((current_time - start_time)); \
		printf "\r\033[KStatus: \033[1;34m%-12s\033[0m | Tempo decorrido: \033[1;32m%02d:%02d\033[0m" "$$status" "$$((elapsed / 60))" "$$((elapsed % 60))"; \
		if [ "$$status" = "InService" ]; then \
			echo "\n\n### [SUCESSO] Endpoint está online!"; \
			break; \
		elif [ "$$status" = "Failed" ]; then \
			echo "\n\n### [ERRO] O deploy falhou. Verifique os logs com 'make logs'."; \
			break; \
		elif [ -z "$$status" ]; then \
			printf "\r\033[KAguardando criação do endpoint..."; \
		fi; \
		sleep 5; \
	done

clean:
	-aws sagemaker delete-endpoint --endpoint-name $(ENDPOINT_NAME)
	-aws sagemaker delete-endpoint-config --endpoint-config-name $(CONFIG_NAME)
	-aws sagemaker delete-model --model-name $(MODEL_NAME)
