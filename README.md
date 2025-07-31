# LangGraph Basics

Welcome to LangGraph Basics! 

## Introduction
In this session, you will learn about the fundamentals of LangGraph through one of our notebooks, as well as a prebuilt agent


## Pre-work

### Clone the LangGraph Basics repo
```
git clone https://github.com/xuro-langchain/langgraph-basics
```

### Create an environment and install dependencies  
```
# Ensure you have a recent version of pip and python installed
$ cd langgraph-101
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

### Running notebooks
Make sure the following command works and opens the relevant notebooks
```
$ jupyter notebook
```

### Set OpenAI API key
* If you don't have an OpenAI API key, you can sign up [here](https://openai.com/index/openai-api/).
*  Set `OPENAI_API_KEY` in the .env file.

## Working with the Pre-built Agent

A prebuilt agent which you can fill in with your own tools and modifications is available at ```agent.py```. The tools and prompts for the agent are in ```tools.py``` and ```prompts.py``` respectively.

Run the agent using:
```
python3 agent.py
```