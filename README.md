# Nifty Collectooor

An agent that continously watches [ArtBlocks](artblocks.io) for new drops and participates in the auction to mint new NFTs.

## Setup:

- For Python development of the AEA collectooor run

      make new_env

- Then 

      pipenv shell

- To run the agent:

      make new_agent
      cd collectooor
      aea run

- To run frontend (on https://localhost:3000):

      cd frontend
      yarn
      yarn start

- To instantiate custom Gnosis Safe
      - add your env variables
      - add network relevant Gnosis contracts
      - add owners and quorum threshold
      - run:
            cd config/safe
            npm i
            npm run build
            npm run deploy



