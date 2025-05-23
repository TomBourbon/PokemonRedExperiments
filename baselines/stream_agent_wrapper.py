import asyncio
import websockets
import json

import gymnasium as gym

from red_gym_env import RedGymEnv
X_POS_ADDRESS, Y_POS_ADDRESS = 0xD362, 0xD361
MAP_N_ADDRESS = 0xD35E

class StreamWrapper(gym.Wrapper):
    def __init__(self, env, stream_metadata={}):
        super().__init__(env)
        self.ws_address = "wss://transdimensional.xyz/broadcast"
        self.stream_metadata = stream_metadata
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.websocket = None
        self.loop.run_until_complete(
            self.establish_wc_connection()
        )
        self.upload_interval = 300
        self.steam_step_counter = 0
        self.env = env
        self.coord_list = []
        if hasattr(env, "pyboy"):
            self.emulator = env.pyboy
        elif hasattr(env, "game"):
            self.emulator = env.game
        else:
            raise Exception("Could not find emulator!")

    def step(self, action):

        x_pos = self.emulator.get_memory_value(X_POS_ADDRESS)
        y_pos = self.emulator.get_memory_value(Y_POS_ADDRESS)
        map_n = self.emulator.get_memory_value(MAP_N_ADDRESS)
        self.coord_list.append([x_pos, y_pos, map_n])

        if self.steam_step_counter >= self.upload_interval:
            self.stream_metadata["extra"] = f"coords: {len(self.env.seen_coords)}"
            self.loop.run_until_complete(
                self.broadcast_ws_message(
                    json.dumps(
                        {
                          "metadata": self.stream_metadata,
                          "coords": self.coord_list
                        }
                    )
                )
            )
            self.steam_step_counter = 0
            self.coord_list = []

        self.steam_step_counter += 1

        return self.env.step(action)

    async def broadcast_ws_message(self, message):
        if self.websocket is None:
            await self.establish_wc_connection()
        if self.websocket is not None:
            try:
                await self.websocket.send(message)
            except websockets.exceptions.WebSocketException as e:
                self.websocket = None

    async def establish_wc_connection(self):
        try:
            self.websocket = await websockets.connect(self.ws_address)
        except:
            self.websocket = None


# # Exemple d'utilisation
# if __name__ == "__main__":
#     # Créez votre environnement gym
#     env = gym.make('RedGymEnv')  # Remplacez par votre environnement souhaité

#     # Enveloppez l'environnement avec StreamWrapper
#     env = StreamWrapper(
#         env,
#         stream_metadata={
#             "user": "super-cool-user",  # Choisissez votre propre nom d'utilisateur
#             "env_id": "CartPole-v1",    # Identifiant de l'environnement
#             "color": "#0033ff",         # Choisissez votre couleur
#             "extra": "Texte supplémentaire", # Tout texte supplémentaire que vous souhaitez afficher
#             "sprite_id": 0,             # Choisissez votre sprite de personnage, de 0 à 50 (optionnel)
#         }
#     )

#     # Maintenant, vous pouvez utiliser l'environnement enveloppé
#     observation = env.reset()
#     for _ in range(1000):
#         env.render()
#         action = env.action_space.sample()  # Remplacez par l'action de votre agent
#         observation, reward, done, info = env.step(action)
#         if done:
#             observation = env.reset()
#     env.close()