import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageRole, FilePurpose, FunctionTool, FileSearchTool, ToolSet
from dotenv import load_dotenv

load_dotenv(override=True)

project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_CONNECTION_STRING"],
    credential=DefaultAzureCredential()
)


# Upload all files in the documents directory
print(f"Uploading files from ./documents ...")
file_ids = [
    project_client.agents.files.upload_and_poll(file_path=os.path.join("./documents", f), purpose=FilePurpose.AGENTS).id
    for f in os.listdir("./documents")
    if os.path.isfile(os.path.join("./documents", f))
]
print(f"Uploaded {len(file_ids)} files.")

# Create a vector store with the uploaded files
vector_store = project_client.agents.vector_stores.create_and_poll(
    data_sources=[],
    name="contoso-pizza-store-information"
)
print(f"Created vector store, vector store ID: {vector_store.id}")


# Create a vector store file batch to process the uploaded files
batch = project_client.agents.vector_store_file_batches.create_and_poll(
    vector_store_id=vector_store.id,
    file_ids=file_ids
)
file_search = FileSearchTool(vector_store_ids=[vector_store.id])

toolset = ToolSet()
toolset.add(file_search)

agent = project_client.agents.create_agent(
    model="gpt-4o",
    name="my-agent",
    instructions=open("instructions.txt").read(),
    top_p=0.7,
    temperature=0.7,
    toolset=toolset  # Add the toolset to the agent
)
print(f"Created agent, ID: {agent.id}")


thread = project_client.agents.threads.create()
print(f"Created thread, ID: {thread.id}")


#Fetch All Messages from the Thread
while True:

    # Get the user input
    user_input = input("You: ")

    # Break out of the loop
    if user_input.lower() in ["exit", "quit"]:
        break

    # Add a message to the thread
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role=MessageRole.USER, 
        content=user_input
    )
    run = project_client.agents.runs.create_and_process(
        thread_id=thread.id, 
        agent_id=agent.id
    )

    messages = project_client.agents.messages.list(thread_id=thread.id)  
    first_message = next(iter(messages), None) 
    if first_message: 
        print(next((item["text"]["value"] for item in first_message.content if item.get("type") == "text"), ""))




project_client.agents.delete_agent(agent.id)
print("Deleted agent")