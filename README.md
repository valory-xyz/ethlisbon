# Nifty Collectooor

An agent that continously watches [ArtBlocks](artblocks.io) for new drops and participates in the auction to mint new NFTs. You can also see the post [here on DevPost](https://devpost.com/software/el-collectooorr).

## Inspiration

Many people want to get access to the upside of projects launching on successful art platforms like Art Blocks but lack the capital and flexibility to build their own collection. El Collectooorr gives people that opportunity.

## What it does

Users add funds to El Collectooorr. Then El Collectooorr watches for new Art Blocks projects to drop. When they drop, El Collectooorr jumps into action, participating in a price auction using a proprietary pricing algorithm. When pieces are won, they are added to the vault. All of this can happen autonomously with zero human interaction, save for adding funds.

## How we built it

We use Gnosis Safe as the vault for the NFTs. The agent is build using the AEA framework of which one of the authors is a maintainer. The frontend it built with React. The agent and frontend are completely separated. The agent does not hold any significant funds (just to pay for transaction fees). Ultimately, we want to implement the agent as a decentralised multi-agent system with the new stack we're building at Valory.

The demo is deployed on Ropsten with the safe here: https://ropsten.etherscan.io/address/0x2cab92c1e9d2a701ca0411b0ff35a0907ca31f7f

The attached example.txt shows a run of the agent from earlier today.

## Challenges we ran into

Documentation of ArtBlocks was quite poor so had to dig into the contracts manually.

## Accomplishments that we're proud of

A simple example which gets an important concept - autonomous applications with on-chain AND off-chain components - across.

## What's next for El Collectooorr

Ultimately we want to make this much more robust in its execution, and permissionless in its extensibility. To achieve this we can use Valory, the project 2 of our team members are working on.

This should be made robust because it's currently dependent on a single bot. Ideas for things which could be extended by other developers permissionlessly:

    improve granularity of price algorithm
    make decisions about how long to hold/what offers to accept etc
    add more art drop platforms

In addition, El Collectooorr could be properly tokenised to give people true access to the upside.

# Setup

- Create and launch a virtual environment. Also, run this during development, everytime you need to re-create and launch the virtual environment and update the dependencies:

      make new_env && pipenv shell

- Run the agent:

      make new_agent
      cd collectooor && aea run

- (Optional) Run the frontend on https://localhost:3000:

      cd frontend && yarn
      yarn start

## Using a custom Gnosis Safe
To instantiate a custom Gnosis Safe:
- Add your env variables.
- Add network relevant Gnosis contracts.
- Add owners and quorum threshold.
- Run:

      cd config/safe && npm i
      npm run build && npm run deploy



