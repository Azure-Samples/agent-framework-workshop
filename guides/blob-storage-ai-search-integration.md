## Azure Blob Storage + AI Search Integration

This guide walks you through setting up a production-ready architecture that connects Azure Blob Storage to Azure AI Search for automated document indexing pipelines.

### Overview

This setup enables:
- **Automatic indexing** - Documents uploaded to Blob Storage are automatically indexed
- **Incremental updates** - Only new or changed documents are re-indexed
- **Managed identity authentication** - Secure, keyless connections between services
- **Built-in skillsets** - Azure AI Search can automatically chunk, embed, and enrich documents

### What You'll Set Up

1. **Azure AI Search service** - For indexing and searching your documents
2. **Storage account** - For storing source documents  
3. **Permissions** - For secure access between services using managed identities

---

#### Introduction to Azure AI Search

**Azure AI Search** is a fully managed search-as-a-service that lets you add sophisticated search capabilities to your apps without managing infrastructure.

**Core capabilities:**
- Full-text search, filtering, faceting, and autocomplete
- **Semantic search** - Understanding meaning and context
- **Vector search** - Similarity matching using embeddings  
- **Hybrid search** - Combining keyword and vector approaches

**Data sources:** Azure Blob Storage, Azure SQL Database, Cosmos DB, or direct REST API uploads. Supports PDFs, Office documents, HTML, JSON, and plain text.

---

#### Prerequisites

Before proceeding with this guide, ensure you have:

- **An Azure AI Foundry project** with a deployed GPT model
- **Identified your resource group in Azure Portal**: You can find the resource group name under **"Project details"** on your project's **"Overview"** page in Foundry.

---

#### Step 1: Create an Azure AI Search Service

1. Navigate to your resource group in the Azure portal and create a new Azure AI Search service resource:
   - Create -> Search for "Azure AI Search"
   - It is recommended to create the search service in the same region as your AI project
   - Select 'Standard' tier for production workloads
	
    ![img1](images/image.png)

2. Navigate to your search service once it is created. Under Settings -> Keys, ensure 'Both' is selected for API access control. Click 'Save'.

    ![img2](images/image1.png)

3. Navigate to Settings -> Identity -> Turn on system-assigned identity -> click 'Save'.

    ![img3](images/image2.png)

4. In Foundry Portal, deploy an embedding model:
   - Select `text-embedding-3-large` and deploy it. This will be used to create the vector embeddings for your documents.

---

#### Step 2: Create a Storage Account

Create a storage account and container to store your source documents. Azure AI Search will connect to this storage to automatically index documents:

1. Create -> Search for "Storage Account" -> Click "Create"

    ![Sample Photo](images/storageacc.png)

2. Once created, navigate to the Storage Account
3. Expand "Data Storage" in the side menu and click on "Containers"
4. Create a new container for your documents (e.g., 'documents')

---

#### Step 3: Configure Managed Identity Permissions

These permissions enable secure, keyless authentication between Azure AI Search and Blob Storage.

##### Search Service -> Storage Account:

1. Navigate to the storage account's **Access Control (IAM)** section. Select 'Add' -> 'Add role assignment'. **Assign the 'Storage Blob Data Reader' role to the search service identity**:

    ![Sample Photo](images/blob-roleassign.jpg)

##### Foundry -> Search Service:

2. Navigate to your **Azure AI Search resource**. Assign two roles to your Foundry project's managed identity: the **'Search Index Data Reader'** role and the **'Search Service Contributor'** role:

    ![searchindex_reader](images/searchindex_reader.jpg)

    ![search_contributor](images/search_contributor.jpg)

##### Search Service -> Foundry:

3. Navigate to your **Foundry** resource. Select Access control (IAM) -> Add Role assignment -> Select **Azure AI Project Manager** role -> Under **Members**, select **Managed identity**, and then select the managed identity of your search service:

    ![pm_role](images/pm_role.png)


##### User Permissions (if needed):

**If you have contributor or higher permissions on the resource group, you inherit these permissions and can skip this section.**

For users without contributor access:

1. **Reader role** on the Azure Subscription level
2. **Cognitive Services OpenAI Contributor** role on the Azure AI Foundry resource
3. **Azure AI Project Manager** role on the Azure AI Foundry resource and project
4. **Storage Blob Data Contributor** role on the Storage Account
5. **Search Service Contributor** role on the Azure AI Search resource

---

#### Step 4: Configure Environment Variables

Add the following to your `.env` file:

```
AZURE_SEARCH_ENDPOINT=https://<search-service-name>.search.windows.net
AZURE_SEARCH_INDEX_NAME=<your-index-name>
SEARCH_API_KEY=<your-search-api-key>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-large
```

You can find the search API key in the Azure Portal under your Search Service -> Settings -> Keys.

---

### Architecture Overview

This setup creates the following architecture:

- **Azure AI Foundry** - Hosts model deployments (GPT-4o, embeddings) and provides API endpoints
- **Azure AI Search** - Provides indexing, vector storage, and semantic search capabilities
- **Azure Blob Storage** - Stores source documents; changes trigger automatic re-indexing

The managed identity connections enable:
- Search service reads documents from Blob Storage
- Search service calls Foundry for embedding generation
- Foundry queries the search index for RAG scenarios

This architecture supports production RAG (Retrieval-Augmented Generation) workloads where documents are automatically processed and made searchable as they're uploaded to storage.
