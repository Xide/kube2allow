app/caps_mapping.json:
	./hack/gen_caps_mapping.sh
	python hack/parse_caps_mapping.py

upload:
	docker build -t sigbilly/kube2allow:latest app
	docker push sigbilly/kube2allow:latest

re:
	minikube delete || true
	minikube start --vm-driver=virtualbox
	make upload
	kubectl apply -f ds.yaml