<!-- PROJECT LOGO -->
<br />
<div align="center">

<h3 align="center">Conversational Product Analytics</h3>

  <p align="center">
    A toolkit for analyzing and improving multi-turn AI conversations through data-driven insights
    <br />
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#examples">Examples</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About The Project

### What is Conversational Product Analytics?
You've built a multi-turn conversational AI, and it works great on the small synthetic dataset you've tested! However, when you launch it, you see that many users are having negative experiences, and every time you fix one issue, two new ones appear.

Enter Conversational Product Analytics: A way to gain deeper insights into how different users experience your conversational AI, understand the gaps in your AI, and systematically improve the user experience.

### Why Product Analytics?

Traditional product analytics tools like Amplitude and PostHog excel at helping teams build better digital products... when those products are static websites or apps. But when it comes to GenAI, their capabilities fall short. Analyzing generic events like "sent message" does not help you understand your users' experiences.

The missing piece is richer, more informative events (e.g. the user asks for clarification, the assistant refuses to answer, or the user expresses frustration). These kinds of insights are essential for understanding and improving the user experience in conversational AI products.

This repository helps you identify which events actually matter, tag each message in your conversational data accordingly, and forward those events to your analytics platform of choice, enabling you to continue using product analytics effectively, even in the era of generative AI.

### What does this repo do?

- **Generate Schema**: Automatically analyze your conversation data to create appropriate event schemas based on your specific use case
- **Event Tagging**: Use LLMs to analyze conversations and tag messages with relevant events
- **Event Upload**: Send tagged conversation data to analytics platforms (Amplitude, PostHog)
- **LLM Judge**: Evaluate conversation quality based on customized criteria
- **(Coming soon)** Advanced Conversational Analytics: Built-in tools for analyzing conversation data

<!-- GETTING STARTED -->
## Getting Started

Here's how to set up the Conversational Product Analytics toolkit.

### Prerequisites

* Python 3.8+
* pip (Python package manager)
* API keys for your chosen LLM provider 
  - [OpenAI](https://platform.openai.com/docs/overview)
  - [Anthropic](https://www.anthropic.com/api) (also via [Amazon Bedrock](https://aws.amazon.com/bedrock/))
* API keys for your analytics platform 
  - [Amplitude](https://amplitude.com/docs/analytics)
  - [PostHog](https://posthog.com/docs/product-analytics)

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/channel-labs/conversational-product-analytics.git
   ```
2. Install Python dependencies
   ```sh
   pip install -r requirements.txt
   ```
3. Set up environment variables for your API keys
   ```sh
   # If using OpenAI
   export OPENAI_API_KEY='your_openai_api_key'

    # If using Anthropic through the Anthropic API
   export ANTHROPIC_API_KEY='your_anthropic_api_key'

   # If using Anthropic through the Amazon Bedrock API
   export AWS_ACCESS_KEY_ID='your_aws_access_key'
   export AWS_SECRET_ACCESS_KEY='your_aws_secret_key'
   export AWS_REGION='your_aws_region' # e.g. us-east-1
   
   # If using Amplitude
   export AMPLITUDE_API_KEY='your_amplitude_api_key'
   
   # If using PostHog
   export POSTHOG_API_KEY='your_posthog_api_key'
   export POSTHOG_HOST='your_posthog_host'
   ```

<!-- USAGE EXAMPLES -->
## Usage

The toolkit provides two main functionalities:

### 1. Generate Event Schema

First, you can use this repo generate a schema that defines what events and properties to track in your conversations:

```sh
python src/generate_schema.py \
  --data-path examples/therapist/example_data.json \
  --data-schema-output-path therapist_schema.yml \
  --model-provider openai \
  --assistant-namer-model gpt-4.1 \
  --event-schema-model o3-mini
```

This will:
- Analyze your conversation data
- Generate a schema defining meaningful events and properties
- Save it to the specified output file

Feel free to modify the resultant schema as needed. We've found the best results occur when domain experts use their expertise to improve upon the LLM's suggested schema.

### 2. Upload Events

After generating a schema, you can process conversations and upload the tagged events to your analytics platform:

```sh
python src/upload_events.py \
  --data-path examples/therapist/example_data.json \
  --data-schema-path therapist_schema.yml \
  --destination posthog \
  --model-provider openai \
  --event-model gpt-4.1
```

This will:
- Process conversations according to your schema
- Use LLMs to identify and tag events
- Upload the events to your chosen analytics platform (Amplitude or PostHog)

### Examples

The tool supports conversation data in multiple formats. See the examples/ directory for examples

- **JSON format**: Structured conversation data where:
  - Each key is a conversation_id
  - Each value is an object with a `messages` array
  - Each message requires `role` and `content` fields
  - Optional message fields: `timestamp` and `message_id`

- **CSV format**: Tabular conversation data with the following columns:
  - Required: either `user_id` or `conversation_id` (at least one is needed)
  - Required: `role` and `content` columns
  - Optional: `message_id` and `timestamp` columns

Data can be loaded from:

- **Local files**: Direct path to your JSON or CSV files
- **Amazon S3**: Use s3:// URI format (e.g., `s3://your-bucket/path/to/conversations.json`)

The repository includes two example datasets to help you get started:

1. **Mental Health Companion** (`examples/therapist/`)
   - Example data: Conversations between users and a therapy assistant
   - Run schema generation:
     ```sh
     python src/generate_schema.py \
       --data-path examples/therapist/example_data.json \
       --data-schema-output-path therapist_schema.yml \
       --model-provider openai \
       --assistant-namer-model gpt-4.1
     ```
   - Run event tagging and upload:
     ```sh
     python src/upload_events.py \
       --data-path examples/therapist/example_data.json \
       --data-schema-path examples/therapist/schema.yml \
       --destination posthog

2. **Tax Advisor** (`examples/tax_advisor/`)
   - Example data: Conversations between users and a tax assistance bot
   - Run schema generation:
     ```sh
     python src/generate_schema.py \
       --data-path examples/tax_advisor/example_data.json \
       --data-schema-output-path tax_advisor_schema.yml
     ```
   - Run event tagging and upload:
     ```sh
     python src/upload_events.py \
       --data-path examples/tax_advisor/example_data.json \
       --data-schema-path examples/tax_advisor/schema.yml \
       --destination posthog
     ```

For S3 data sources, ensure you have AWS credentials configured and use the S3 URI format:

```sh
python src/generate_schema.py \
  --data-path s3://your-bucket/conversations/data.json \
  --data-schema-output-path my_schema.yml \
  --model-provider openai
```

<!-- ROADMAP -->
## Roadmap

- [x] Schema generation
- [x] Event tagging with LLMs
- [x] Analytics platform integration (Amplitude, PostHog)
- [ ] Built-in analytics dashboard
- [ ] Conversation improvement recommendations
- [ ] Support for more LLM providers and analytics platforms

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. Otherwise, feel free to start a discussion or open an issue here on GitHub, and we'll review shortly.

Don't forget to give the project a star! Thanks again!

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<!-- CONTACT -->
## Contact

Create by [Channel Labs](https://channellabs.ai/)

Interested in understand and improving your AI's behavior even further? Contact scott@channellabs.ai for any inquiries.
