import requests

url = "https://discord.com/api/v8/applications/917705441054687262/commands"

json = {
    "name": "blep",
    "type": 1,
    "description": "Send a random adorable animal photo",
    "options": [
        {
            "name": "animal",
            "description": "The type of animal",
            "type": 3,
            "required": True,
            "choices": [
                {
                    "name": "Dog",
                    "value": "animal_dog"
                },
                {
                    "name": "Cat",
                    "value": "animal_cat"
                },
                {
                    "name": "Penguin",
                    "value": "animal_penguin"
                }
            ]
        },
        {
            "name": "only_smol",
            "description": "Whether to show only baby animals",
            "type": 5,
            "required": False
        }
    ]
}

headers = {
    "Authorization": f"Bot OTE3NzA1NDQxMDU0Njg3MjYy.Ya8lyw.cewDWv2IimxAmHTW80L3oPJb7Nc"
}
print(f"{headers=}")
print(requests.post(url, headers=headers, json=json))
