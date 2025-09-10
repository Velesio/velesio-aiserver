mkdir -p undreamai-server
cd undreamai-server
wget https://github.com/undreamai/LlamaLib/releases/download/v1.2.6/undreamai-v1.2.6-llamacpp-full.zip
wget https://github.com/undreamai/LlamaLib/releases/download/v1.2.6/undreamai-v1.2.6-server.zip
unzip undreamai-v1.2.6-llamacpp-full.zip
unzip undreamai-v1.2.6-server.zip
mv undreamai-server/linux-cuda-cu12.2.0-full/* .
rm -rf undreamai-server