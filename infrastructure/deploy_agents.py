import boto3
import yaml

REGION = "eu-central-1"

prompts = ''
with open('../src/schema/prompts.yaml', 'r') as file:
    prompts = yaml.safe_load(file)


# ToDo: Change with your Role Arn for bedrock agent from CDK
agent_resource_role_arn = 'arn:aws:iam::792216152683:role/InfrastructureStack-BedrockAgentRole7C982E0C-g76aZYH1OPTK'

agent_client = boto3.client("bedrock-agent", region_name=REGION)

agent_description = prompts['agent_web_search_instructions']['prompt']
instruction = prompts['agent_web_search_instructions']['prompt']

# creation of a Bedrock agent via the Bedrock agent build api
args = {
    'agentName': 'InternetSearchAgent',  # unique name of an agent
    'agentResourceRoleArn': agent_resource_role_arn,
    'foundationModel': 'anthropic.claude-v2:1',
    'idleSessionTTLInSeconds': int(60 * 15),
    'instruction': instruction,
    'description': agent_description
}
print('deploy agent...')
response = agent_client.create_agent(**args)

agent_id = response['agent']['agentId']

response = agent_client.create_agent_alias(
    agentAliasName='alias',
    agentId=agent_id
)

print(f'Agent is deployed., AgentId: {agent_id}, AgentAliasId: {response}')
