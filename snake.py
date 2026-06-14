import random
import sys
from collections import deque
from dataclasses import dataclass

import pygame


# -----------------------------
# Settings
# -----------------------------
CELL_SIZE = 24
GRID_WIDTH = 32
GRID_HEIGHT = 24

SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE
FPS = 6

BG = (20, 20, 24)
GRID = (35, 35, 42)
FOOD_COLOR = (230, 70, 70)
TEXT = (235, 235, 235)

P1_COLOR = (70, 200, 120)
P1_HEAD = (120, 255, 170)

P2_COLOR = (80, 150, 240)
P2_HEAD = (140, 200, 255)


def add_pos(a, b):
	return a[0] + b[0], a[1] + b[1]


def opposite(a, b):
	return a[0] == -b[0] and a[1] == -b[1]


def random_empty_cell(snakes):
	occupied = set()
	for snake in snakes:
		occupied.update(snake.body)

	while True:
		pos = random.randrange(GRID_WIDTH), random.randrange(GRID_HEIGHT)
		if pos not in occupied:
			return pos


class Snake:
	def __init__(self, body, direction, color, head_color, name):
		self.body = deque(body)
		self.direction = direction
		self.color = color
		self.head_color = head_color
		self.name = name
		self.score = 0
		self.alive = True

	@property
	def head(self):
		return self.body[0]

	def set_direction(self, direction):
		if not opposite(direction, self.direction):
			self.direction = direction

	def move(self, grow=False):
		if not self.alive:
			return

		new_head = add_pos(self.head, self.direction)
		self.body.appendleft(new_head)

		if not grow:
			self.body.pop()
		else:
			self.score += 1

	def draw(self, screen):
		for i, segment in enumerate(self.body):
			rect = pygame.Rect(
				segment[0] * CELL_SIZE,
				segment[1] * CELL_SIZE,
				CELL_SIZE,
				CELL_SIZE,
			)
			color = self.head_color if i == 0 else self.color
			pygame.draw.rect(screen, color, rect.inflate(-2, -2), border_radius=5)


# -----------------------------
# Game logic
# -----------------------------
def reset_game(is_host:bool):
	p1 = Snake(
		body=[(8, 12), (7, 12), (6, 12)],
		direction=(1, 0),
		color=P1_COLOR,
		head_color=P1_HEAD,
		name="Player 1",
	)

	p2 = Snake(
		body=[(23, 12), (24, 12), (25, 12)],
		direction=(-1, 0),
		color=P2_COLOR,
		head_color=P2_HEAD,
		name="Player 2",
	)

	# problem : how do we assign player places ?
	# easier would be to just sort by steam id
	# for now we just swap snakes for host
	if is_host: p1, p2 = p2, p1

	food = random_empty_cell([p1, p2])
	return p1, p2, food, False


def out_of_bounds(pos):
	x, y = pos
	return x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT


def resolve_collisions(p1, p2):
	snakes = [p1, p2]

	# Wall collisions
	for snake in snakes:
		if out_of_bounds(snake.head):
			snake.alive = False

	# Self collisions
	for snake in snakes:
		if snake.head in list(snake.body)[1:]:
			snake.alive = False

	# Snake-vs-snake collisions
	if p1.head in list(p2.body):
		p1.alive = False

	if p2.head in list(p1.body):
		p2.alive = False

	# Head-on collision
	if p1.head == p2.head:
		p1.alive = False
		p2.alive = False

	return not p1.alive or not p2.alive


def draw_grid(screen):
	for x in range(0, SCREEN_WIDTH, CELL_SIZE):
		pygame.draw.line(screen, GRID, (x, 0), (x, SCREEN_HEIGHT))

	for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
		pygame.draw.line(screen, GRID, (0, y), (SCREEN_WIDTH, y))


def draw_food(screen, food):
	center = (
		food[0] * CELL_SIZE + CELL_SIZE // 2,
		food[1] * CELL_SIZE + CELL_SIZE // 2,
	)
	pygame.draw.circle(screen, FOOD_COLOR, center, CELL_SIZE // 3)


def draw_text(screen, font, text, x, y, color=TEXT):
	surf = font.render(text, True, color)
	screen.blit(surf, (x, y))

def draw_centered_text(screen, font, text, y, color=TEXT):
	surf = font.render(text, True, color)
	rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
	screen.blit(surf, rect)


def run_game(screen, lobby):
	netUtils = steam.SteamNetworkingUtils()
	status = steam.SteamRelayNetworkStatus()
	t = time.time() + 3.0
	while ((availability := netUtils.GetRelayNetworkStatus(status.ptr)) >= 0
		and availability != steam.ESteamNetworkingAvailability.Current
		and time.time() < t):
		time.sleep(0.05)
	print("availability", availability, status.debugMsg)

	relay = steam.SteamNetworkingMessages()
	members = lobby.members

	is_host = lobby.owner_id == local_id

	p1, p2, food, game_over = reset_game(is_host)

	p1_name = members[local_id]
	p2_name = 'Guest'

	peer = steam.SteamNetworkingIdentity()
	recv_msgs = (ctypes.c_void_p * 16)()

	def accept_session(P2PSessionRequest):
		print('accept_session')
		id = P2PSessionRequest.steamIDRemote
		if id in members: relay.AcceptSessionWithUser(id)

	_ = steam.OnP2PSessionRequest(accept_session)

	for id, name in members.items():
		if id == local_id: continue
		print('peer is', name)
		p2_name = name
		peer.SetSteamID(id)
		assert not peer.IsInvalid()

	while True:
		print('', flush=True)
		clock.tick(FPS)

		if not game_over:
			p1_will_eat = add_pos(p1.head, p1.direction) == food
			p2_will_eat = add_pos(p2.head, p2.direction) == food

			p1.move(grow=p1_will_eat)
			p2.move(grow=p2_will_eat)

			if p1_will_eat or p2_will_eat:
				food = random_empty_cell([p1, p2])

			game_over = resolve_collisions(p1, p2)


		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				quit_game()

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					quit_game()

				if game_over and event.key == pygame.K_SPACE:
					p1, p2, food, game_over = reset_game(is_host)

				# Player 1: WASD
				if event.key == pygame.K_w:
					p1.set_direction((0, -1))
				elif event.key == pygame.K_s:
					p1.set_direction((0, 1))
				elif event.key == pygame.K_a:
					p1.set_direction((-1, 0))
				elif event.key == pygame.K_d:
					p1.set_direction((1, 0))

				# Player 2: Arrow keys
				elif event.key == pygame.K_UP:
					p2.set_direction((0, -1))
				elif event.key == pygame.K_DOWN:
					p2.set_direction((0, 1))
				elif event.key == pygame.K_LEFT:
					p2.set_direction((-1, 0))
				elif event.key == pygame.K_RIGHT:
					p2.set_direction((1, 0))

		# send state
		values = [*p1.head, *p1.direction]  # head_x, head_y, dir_x, dir_y
		payload = ",".join(map(str, values)).encode()
		buf = ctypes.create_string_buffer(payload)
		# peer, packet*, packet size, communication flags, channel 
		result = relay.SendMessageToUser(
			peer,
			ctypes.addressof(buf),
			len(payload),
			steam.nSteamNetworkingSend_ReliableNoNagle,
			0,
		)
		if result != steam.EResult.OK:
			print("SendMessageToUser failed:", result)

		# retrieve peer state
		while True:
			n = relay.ReceiveMessagesOnChannel(0, ctypes.addressof(recv_msgs), len(recv_msgs))
			if n <= 0:break

			for i in range(n):
				msg_ptr = recv_msgs[i]
				msg = steam.SteamNetworkingMessage.from_ptr(msg_ptr)

				data = steam.to_bytes(msg.pData, msg.cbSize)
				text = data.decode()
				print(text)
				head_x, head_y, dir_x, dir_y = map(int, text.split(","))

				p2.body[0] = (head_x, head_y)
				p2.direction = (dir_x, dir_y)

				#msg.Release()

		screen.fill(BG)
		draw_grid(screen)
		draw_food(screen, food)
		p1.draw(screen)
		p2.draw(screen)
		
		score_text = f"{p1_name}: {p1.score}   {p2_name}: {p2.score}"
		surf = font.render(score_text, True, TEXT)
		screen.blit(surf, (12, 8))

		if game_over:
			if p1.alive and not p2.alive:
				msg = f"{p1_name} wins!"
			elif p2.alive and not p1.alive:
				msg = f"{p2_name} wins!"
			else:
				msg = "Draw!"

			msg2 = "Press SPACE to restart or ESC to quit"

			draw_centered_text(screen, big_font, msg, SCREEN_HEIGHT // 2 - 30, TEXT)
			draw_centered_text(screen, font, msg2, SCREEN_HEIGHT // 2 + 25, TEXT)

		pygame.display.flip()


# -----------------------------
# Simple lobby menu
# -----------------------------

import steamworks as steam
import ctypes
import time

MAX_LOBBY_MEMBERS = 2

def quit_game():
	global lobby_id
	if lobby_id and (mm := steam.SteamMatchmaking()):
		mm.LeaveLobby(lobby_id)
		lobby_id = None
	steam.shutdown()
	pygame.quit()
	sys.exit()


def pump_callbacks(seconds=0.25):
	end = time.time() + seconds

	while time.time() < end:
		steam.RunCallbacks()
		time.sleep(0.01)

def get_call_state(call, result, failed=None):
	if failed == None: failed = ctypes.c_bool(False)
	utils = steam.SteamUtils()
	result_type = type(result)

	ok = utils.GetAPICallResult(
		hSteamAPICall=call,
		pCallback=result.ptr,
		cubCallback=result_type.nbytes,
		iCallbackExpected=result_type.callback_id,
		pbFailed=ctypes.addressof(failed),
	)

	if ok:
		if failed.value:
			raise RuntimeError("Steam API call failed")
		return result

	return False


def wait_call_result(call, result, timeout=15.0):
	failed = ctypes.c_bool(False)

	end = time.time() + timeout

	while time.time() < end:
		steam.RunCallbacks()

		if(res := get_call_state(call, result, failed)):
			return res

		time.sleep(0.01)

	raise TimeoutError("Steam API call timed out")


def get_lobby_members(lobby_id):
	matchmaking = steam.SteamMatchmaking()
	friends = steam.SteamFriends()

	count = matchmaking.GetNumLobbyMembers(lobby_id)
	members = {}

	for i in range(count):
		member_id = matchmaking.GetLobbyMemberByIndex(lobby_id, i) # CSteamID
		member_name = friends.GetFriendPersonaName(member_id)
		members[member_id] = member_name

	return members

@dataclass
class Lobby:
	lobby_id : SteamId
	owner_id : SteamId
	name     : str
	members  : dict[SteamId, str]

def lobby_to_dict(lobby_id, default_name="Steam lobby"):
	matchmaking = steam.SteamMatchmaking()

	owner_id = matchmaking.GetLobbyOwner(lobby_id)

	name = matchmaking.GetLobbyData(lobby_id, "name")
	if not name: name = default_name

	return Lobby(lobby_id, owner_id, name, get_lobby_members(lobby_id) )


def create_lobby():
	global lobby_id
	matchmaking = steam.SteamMatchmaking()

	call = matchmaking.CreateLobby(
		steam.ELobbyType.Public,
		MAX_LOBBY_MEMBERS,
	)

	result = wait_call_result(call, steam.LobbyCreated())

	if result.eResult != steam.EResult.OK:
		raise RuntimeError(f"Could not create lobby: {result.eResult}")

	lobby_id = result.ulSteamIDLobby

	username = steam.SteamFriends().GetPersonaName()

	matchmaking.SetLobbyData(lobby_id, "name", f"{username}'s lobby")
	matchmaking.SetLobbyJoinable(lobby_id, True)

	pump_callbacks(0.25)

	return lobby_to_dict(lobby_id, default_name="Your lobby")


def join_lobby(lobby_name):
	global lobby_id
	matchmaking = steam.SteamMatchmaking()
	
	if lobby_name.isdigit():
		lobby_id = steam.SteamID(int(lobby_id_text))
	else:
		matchmaking.AddRequestLobbyListStringFilter(
			"name", lobby_name, steam.ELobbyComparison.Equal,
		)
		call = matchmaking.RequestLobbyList()
		result = wait_call_result(call, steam.LobbyMatchList())

		if result.nLobbiesMatching < 1:
			raise RuntimeError( f"Did not find lobby: {lobby_name}" )

		lobby_id = matchmaking.GetLobbyByIndex(0)

	call = matchmaking.JoinLobby(lobby_id)
	result = wait_call_result(call, steam.LobbyEnter())

	if result.EChatRoomEnterResponse != steam.EChatRoomEnterResponse.Success:
		raise RuntimeError( f"Could not join lobby: {result.EChatRoomEnterResponse}" )

	joined_lobby_id = steam.SteamID(result.ulSteamIDLobby)

	return lobby_to_dict(joined_lobby_id, default_name="Remote Host's lobby")


def run_join_lobby_input(screen):
	lobby_name = ""

	while True:
		clock.tick(FPS)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				quit_game()

			if event.type != pygame.KEYDOWN:
				continue

			if event.key == pygame.K_ESCAPE:
				return None

			if event.key == pygame.K_BACKSPACE:
				lobby_name = lobby_name[:-1]

			elif event.key == pygame.K_RETURN:
				return join_lobby(lobby_name)

			elif event.unicode and event.unicode.isprintable():
				lobby_name += event.unicode

		screen.fill(BG)

		draw_centered_text(screen, big_font, "Join Lobby", 120)
		draw_centered_text(screen, font, "Enter a lobby ID or name:", 210)

		box = pygame.Rect(SCREEN_WIDTH // 2 - 160, 250, 320, 44)
		pygame.draw.rect(screen, GRID, box, border_radius=6)
		pygame.draw.rect(screen, TEXT, box, width=2, border_radius=6)

		shown_text = lobby_name if lobby_name else "type here..."
		color = TEXT if lobby_name else (140, 140, 150)

		draw_text(screen, font, shown_text, box.x + 12, box.y + 12, color)

		draw_centered_text(
			screen,
			font,
			"ENTER: join   BACKSPACE: delete   ESC: back",
			SCREEN_HEIGHT - 48,
		)

		pygame.display.flip()


def run_lobby_room(screen, lobby):
	matchmaking = steam.SteamMatchmaking()
	lobby_id = lobby.lobby_id
	owner_id = lobby.owner_id

	is_host = owner_id == local_id
	owner_ready = False

	def update_members(LobbyChatUpdate_t):
		nonlocal lobby
		lobby.members = get_lobby_members(lobby_id)

	def update_ready(LobbyDataUpdate_t):
		nonlocal owner_ready
		owner_ready = matchmaking.GetLobbyMemberData(lobby_id, owner_id, 'ready');

	u1 = steam.OnLobbyChatUpdate(update_members)
	u2 = steam.OnLobbyDataUpdate(update_ready)

	while True:
		clock.tick(FPS)
		steam.RunCallbacks()

		if owner_ready: return lobby

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				quit_game()


			if event.type != pygame.KEYDOWN:
				continue

			if event.key == pygame.K_ESCAPE:
				return None

			if is_host and event.key == pygame.K_RETURN:
				matchmaking.SetLobbyMemberData(lobby_id, 'ready', 'True');

		screen.fill(BG)

		role = "Host" if is_host else "Client"

		draw_centered_text(screen, big_font, "Lobby", 90)
		draw_centered_text(screen, font, f"Lobby ID: {lobby_id}   Role: {role}", 145)

		panel = pygame.Rect(SCREEN_WIDTH // 2 - 190, 230, 380, 220)
		pygame.draw.rect(screen, GRID, panel, border_radius=8)

		draw_text(screen, font, "Members", panel.x + 24, panel.y + 22)

		for i, member in enumerate(lobby.members.items()):
			id, name = member
			suffix = " [host]" if id == owner_id else ""
			color = P1_HEAD if id == local_id else TEXT

			draw_text(
				screen,
				font,
				f"{i + 1}. {name}{suffix}",
				panel.x + 36,
				panel.y + 62 + i * 34,
				color,
			)

		draw_centered_text(screen, font, "ENTER: start game   ESC: leave lobby", SCREEN_HEIGHT - 78)

		pygame.display.flip()


def run_lobby_menu(screen):
	global lobby_id
	lobby_id = None

	menu_items = [
		"Create Lobby",
		"Join Lobby",
		"Quit",
	]

	selected_index = 0

	while True:
		clock.tick(FPS)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				quit_game()

			if event.type != pygame.KEYDOWN:
				continue

			if event.key == pygame.K_ESCAPE:
				quit_game()

			elif event.key == pygame.K_UP:
				selected_index = (selected_index - 1) % len(menu_items)

			elif event.key == pygame.K_DOWN:
				selected_index = (selected_index + 1) % len(menu_items)

			elif event.key == pygame.K_RETURN:
				choice = menu_items[selected_index]

				if choice == "Create Lobby":
					lobby = create_lobby()
					ready_lobby = run_lobby_room(screen, lobby)

					if ready_lobby is not None:
						return ready_lobby

				elif choice == "Join Lobby":
					lobby = run_join_lobby_input(screen)

					if lobby is not None:
						ready_lobby = run_lobby_room(screen, lobby)

						if ready_lobby is not None:
							return ready_lobby

				elif choice == "Quit":
					quit_game()


		screen.fill(BG)

		draw_centered_text(screen, big_font, "Two Player Snake", 120)
		draw_centered_text(screen, font, "Steam lobby prototype", 165)

		start_y = 250

		for i, item in enumerate(menu_items):
			color = P1_HEAD if i == selected_index else TEXT
			prefix = "> " if i == selected_index else "  "
			draw_centered_text(screen, font, prefix + item, start_y + i * 42, color)

		draw_centered_text(
			screen,
			font,
			"UP/DOWN: select   ENTER: confirm   ESC: quit",
			SCREEN_HEIGHT - 48,
		)
		pygame.display.flip()



# -----------------------------
# Main
# -----------------------------
def main():
	global clock, font, big_font, local_id
	#try:
	steam.init()
	pygame.init()
	pygame.display.set_caption("Two Player Snake")

	# start this asap
	netUtils = steam.SteamNetworkingUtils()
	netUtils.InitRelayNetworkAccess()

	screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
	clock = pygame.time.Clock()

	font = pygame.font.SysFont(None, 30)
	big_font = pygame.font.SysFont(None, 56)

	local_id = steam.SteamUser().GetSteamID()
	lobby = run_lobby_menu(screen)

	run_game(screen, lobby)

	#except Exception as ex:
	#	print('Error:', ex)
	#finally:
	#	quit_game()


if __name__ == "__main__":
	main()