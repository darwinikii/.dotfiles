#!/usr/bin/env python3
import gi

gi.require_version("Playerctl", "2.0")
from gi.repository import Playerctl, GLib
from gi.repository.Playerctl import Player
import argparse
import logging
import sys
import signal
import gi
import json
import os
from typing import List

logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    logger.info("Received signal to stop, exiting")
    sys.stdout.write("\n")
    sys.stdout.flush()
    # loop.quit()
    sys.exit(0)


class PlayerManager:
    def __init__(self, selected_player=None, playeraudio=False):
        self.manager = Playerctl.PlayerManager()
        self.loop = GLib.MainLoop()
        self.manager.connect(
            "name-appeared", lambda *args: self.on_player_appeared(*args)
        )
        self.manager.connect(
            "player-vanished", lambda *args: self.on_player_vanished(*args)
        )

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        self.selected_player = selected_player
        self.current_player = None

        self.playeraudio = playeraudio

        self.init_players()

    def init_players(self):
        for player in self.manager.props.player_names:
            if self.selected_player is not None and self.selected_player != player.name:
                logger.debug(f"{player.name} is not the filtered player, skipping it")
                continue
            self.init_player(player)

    def run(self):
        logger.info("Starting main loop")
        self.show_most_important_player()
        self.loop.run()

    def init_player(self, player):
        logger.info(f"Initialize new player: {player.name}")
        player = Playerctl.Player.new_from_name(player)

        if self.playeraudio:
            supported = True
            try:
                player.set_volume(player.props.volume)
            except Exception as e:
                supported = False

            player.volume_supported = supported

            if supported:
                player.connect("volume", self.on_volume_changed, None)
                # self.on_volume_changed(player, player.props.volume)

        player.connect("playback-status", self.on_playback_status_changed, None)
        player.connect("metadata", self.on_metadata_changed, None)

        self.manager.manage_player(player)
        self.on_metadata_changed(player, player.props.metadata)

    def get_players(self) -> List[Player]:
        return self.manager.props.players

    def write_output(self, text, player):
        logger.debug(f"Writing output: {text}")

        output = {
            "text": text,
            "class": player.props.player_name,
            "alt": player.props.player_name,
        }

        if (
            player.props.player_name == "firefox"
            and "xesam:url" in player.props.metadata.keys()
            and "youtube" in player.props.metadata["xesam:url"]
        ):
            output["class"] = "youtube"
            output["alt"] = "youtube"

        sys.stdout.write(json.dumps(output) + "\n")
        sys.stdout.flush()

    def clear_output(self):
        sys.stdout.write("\n")
        sys.stdout.flush()

    def on_volume_changed(self, player, volume, _=None):
        new_player = self.get_first_playing_player()
        if (
            new_player is not None
            and player.props.player_name != new_player.props.player_name
        ):
            player = new_player
            volume = new_player.props.volume

        if player.props.volume > 0.65:
            text = ""
        elif player.props.volume > 0:
            text = ""
        elif player.props.volume == 0:
            text = ""
        else:
            text = ""

        text += f" {round(player.props.volume * 100)}%"

        if not player.volume_supported:
            text = ""
        self.write_output(text, player)

    def on_playback_status_changed(self, player, status, _=None):
        logger.debug(
            f"Playback status changed for player {player.props.player_name}: {status}"
        )

        if status == 0 or status == 1:
            self.on_metadata_changed(player, player.props.metadata)

    def get_first_playing_player(self):
        players = self.get_players()
        logger.debug(f"Getting first playing player from {len(players)} players")
        if len(players) > 0:
            player_names = [player.props.player_name for player in players]

            if "firefox" in player_names:
                index = player_names.index("firefox")
                firefox = players[index]
                if (
                    "mpris:length" in firefox.props.metadata.keys()
                    and "xesam:url" in firefox.props.metadata.keys()
                    and "www.youtube.com/watch" in firefox.props.metadata["xesam:url"]
                ):
                    return firefox

            if "spotify" in player_names:
                index = player_names.index("spotify")
                spotify = players[index]
                return spotify
        else:
            logger.debug("No players found")

            return None

    def show_most_important_player(self):
        logger.debug("Showing most important player")
        # show the currently playing player
        # or else show the first paused player
        # or else show nothing
        new_player = self.get_first_playing_player()

        if new_player is not None:
            self.current_player = new_player
        else:
            self.clear_output()

    def on_metadata_changed(self, player, metadata, _=None):
        new_player = self.get_first_playing_player()
        if (
            new_player is not None
            and player.props.player_name != new_player.props.player_name
        ):
            player = new_player
            metadata = new_player.props.metadata

        if player.props.status == "Playing":
            players = self.get_players()

            for x in players:
                if x.props.player_name != player.props.player_name:
                    try:
                        x.pause()
                    except:
                        pass

        logger.debug(f"Metadata changed for player {player.props.player_name}")
        player_name = player.props.player_name
        artist = player.get_artist()
        title = player.get_title()

        artist = artist if artist != "" else None
        title = title if title != "" else None

        track_info = ""
        if (
            player_name == "spotify"
            and "mpris:trackid" in metadata.keys()
            and ":ad:" in player.props.metadata["mpris:trackid"]
        ):
            track_info = "Advertisement"
        if title == "Advertisement":
            track_info = "Advertisement"
        elif artist is not None and title is not None:
            track_info = f"{artist} - {title}"
            if len(track_info) > 40:
                track_info = artist
        elif artist is None and title is None:
            return
        else:
            track_info = title

        track_info = str(track_info).replace("&", "&amp;")

        if self.playeraudio:
            if player.props.volume > 0.65:
                text = ""
            elif player.props.volume > 0:
                text = ""
            elif player.props.volume == 0:
                text = ""
            else:
                text = ""

            text += f" {round(player.props.volume * 100)}%"

            if not player.volume_supported:
                text = ""
            self.write_output(text, player)
        elif track_info:
            if player.props.status == "Playing":
                track_info = " " + track_info
            else:
                track_info = " " + track_info

            self.write_output(track_info, player)

    def on_player_appeared(self, _, player):
        logger.info(f"Player has appeared: {player.name}")
        if player is not None and (
            self.selected_player is None or player.name == self.selected_player
        ):
            self.init_player(player)
            self.show_most_important_player()
        else:
            logger.debug(
                "New player appeared, but it's not the selected player, skipping"
            )

    def on_player_vanished(self, _, player):
        logger.info(f"Player {player.props.player_name} has vanished")

        self.show_most_important_player()


def parse_arguments():
    parser = argparse.ArgumentParser()

    # Increase verbosity with every occurrence of -v
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Define for which player we"re listening
    parser.add_argument("--player")

    parser.add_argument("--enable-logging", action="store_true")

    parser.add_argument("--play-pause", action="store_true")
    parser.add_argument("--next", action="store_true")
    parser.add_argument("--prev", action="store_true")

    parser.add_argument("--playeraudio", action="store_true")

    parser.add_argument("--mute", action="store_true")
    parser.add_argument("--volume-up", action="store_true")
    parser.add_argument("--volume-down", action="store_true")

    return parser.parse_args()


def main():
    arguments = parse_arguments()
    # Initialize logging
    if arguments.enable_logging:
        logfile = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "media-player.log"
        )
        logging.basicConfig(
            filename=logfile,
            level=logging.DEBUG,
            format="%(asctime)s %(name)s %(levelname)s:%(lineno)d %(message)s",
        )

    # Logging is set by default to WARN and higher.
    # With every occurrence of -v it's lowered by one
    logger.setLevel(max((3 - arguments.verbose) * 10, 0))

    logger.info("Creating player manager")
    if arguments.player:
        logger.info(f"Filtering for player: {arguments.player}")
    if (
        arguments.play_pause
        or arguments.next
        or arguments.prev
        or arguments.mute
        or arguments.volume_up
        or arguments.volume_down
    ):
        player = PlayerManager(arguments.player)
        selected = player.get_first_playing_player()
        if selected and arguments.play_pause:
            try:
                selected.play_pause()
            except Exception as e:
                os.system(
                    f'notify-send --app-name={selected.props.player_name} "{"Play-Pause not available now."}"'
                )
        elif selected and arguments.next:
            try:
                selected.next()
            except Exception as e:
                os.system(
                    f'notify-send --app-name={selected.props.player_name} "{"Next not available now."}"'
                )
        elif selected and arguments.prev:
            try:
                selected.previous()
            except Exception as e:
                os.system(
                    f'notify-send --app-name={selected.props.player_name} "{"Previous not available now."}"'
                )
        elif selected and arguments.mute:
            if selected.props.volume == 0:
                selected.set_volume(1)
            else:
                selected.set_volume(0)
        elif selected and arguments.volume_up:
            selected.set_volume(abs(selected.props.volume + 0.05))
        elif selected and arguments.volume_down:
            selected.set_volume(abs(selected.props.volume - 0.05))

        return

    player = PlayerManager(arguments.player, arguments.playeraudio)
    player.run()


if __name__ == "__main__":
    main()
