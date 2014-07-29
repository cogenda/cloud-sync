# On Linux (tested only on Ubuntu), use this script to generate secure deployment key

if [[ ! $(which travis) ]]
then
  gem install travis
fi
# To generate secure SSH deploy key for a github repo to be used from Travis
base64 --wrap=0 ~/.ssh/id_rsa_deploy > ~/.ssh/id_rsa_deploy_base64
ENCRYPTION_FILTER="echo \$(echo \"- secure: \")\$(travis encrypt \"\$FILE='\`cat $FILE\`'\" -r cogenda/cogenda-web)"
split --bytes=100 --numeric-suffixes --suffix-length=2 --filter="$ENCRYPTION_FILTER" ~/.ssh/id_rsa_deploy_base64 id_rsa_
