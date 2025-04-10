import topgg

import config


@topgg.endpoint("/webhook", topgg.WebhookType.BOT, config.VOTING_KEY)
def endpoint(
    vote_data: topgg.BotVoteData,
):
    print("Received a vote!", vote_data)
