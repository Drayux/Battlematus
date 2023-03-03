# Hook the game
# *Specify the player stats / mob (location maybe?)
# Start a fight
#   Check turn number, health values, etc
#   Cast the singular spell
#   If spell still there, I fizzled
#   Else check new health values

import asyncio
import json
import sys
import time
import wizwalker

class CombatHandler(wizwalker.combat.CombatHandler):
    # Override default method to exit if handle_round specifies
    async def handle_combat(self):
        self.combatData = []
        # self.fizzled = True
        while await self.in_combat():
            await self.wait_for_planning_phase()
            self.roundNumber = await self.round_number()
            print("\nRound:", self.roundNumber)

            ret = await self.handle_round()
            if ret > 0:
                self._spell_check_boxes = None
                return
            elif ret < 0: break

            print("Waiting for next round...")
            await self.wait_until_next_round(self.roundNumber)

        # If we made it here, we are unexpectedly out of combat
        # So throw out data
        # print("Something unexpected happened, tossing data!!")
        self._spell_check_boxes = None
        self.combatData = None

    # Subroutine of super.handle_combat()
    # Returns 0 if combat should continue
    # Returns 1 if data has been collected
    # Returns -1 if something unexpected has happened
    async def handle_round(self):
        # If there are more than three members some wizard joined
        # Toss out the data
        members = await self.get_members()
        if len(members) > 3:
            print("Too many combatants, another player must have joined!")
            return -1

        roundData = {}
        playerData = {}
        opponentData = {}

        # Populate round data
        roundData['round'] = self.roundNumber
        roundData['time'] = int(time.time())
        roundData['client'] = playerData
        roundData['opponent'] = opponentData

        await asyncio.sleep(0.5)    # Potential fix for combat member becoming invalid

        # Populate player data
        player = await self.get_client_member()
        playerData['health'] = await player.health()
        playerData['mana'] = await player.mana()
        playerData['pips'] = await player.normal_pips()

        # Populate opponent data
        # TODO: collect data for all members and not a specific one
        assert(self.target)
        assert(self.spell)
        try: opponent = await self.get_member_named(self.target)
        except ValueError:
            print(f"Failed to find target: {self.target}")
            return -1

        opponentData['health'] = await opponent.health()
        opponentData['pips'] = await opponent.normal_pips()

        # opponentStats = await opponent.get_stats()
        # test = await opponentStats.block_percent_by_school()
        # for x in test: print(x)
        # part = await opponent.get_participant()
        # rot = await part.rotation()
        # await part.write_rotation(rot + 2)

        # Save the round data
        self.combatData.append(roundData)
        print("State:", str(roundData))
        # print()

        # Determine if collection is complete (currently does the boss have full health or not)
        bossMaxHealth = await opponent.max_health()
        if bossMaxHealth != await opponent.health():
            # self.fizzled = False
            return 1

        # Flee if we are about to die
        elif playerData['health'] < 300:
            print("Health dangerously low, resetting")
            return 1

        # if self.roundNumber > 1: return 1

        # Select spell
        await asyncio.sleep(0.5)    # Potential fix for the spell selector occasionally skipping a round
        if await self.attempt_cast(self.spell, on_member = self.target): pass
        # if await self.attempt_cast("Scarab", on_member = "Foulgaze"): pass
        else:
            print("Failed to cast spell, passing")
            await self.client.mouse_handler.click_window_with_name("Focus")  # Pass
            return -1

        return 0        # return 0 to continue fighting


# Simple login check
async def inGame(client):
    l = await client.root_window.get_windows_with_type("WizardCharacterSelect")
    # print("In game:", len(l) == 0)
    return len(l) == 0


# Selects character from login screen if logged out
# If loop, keep refreshing until logged out (sometimes game freezes and takes a great deal of time)
# ^^call with loop = loopCount > 1 to avoid getting stuck if client is in game at start of automation (so that wizwalker will hook and assuming no logout called)
async def login(client, loop = True):
    # Currently no check if game already logged out
    while await inGame(client):
        if not loop: return
        await asyncio.sleep(1.0)

    # Assume button exists
    # playButton = await client.root_window.get_windows_with_name("btnPlay")[0]
    await client.mouse_handler.click_window_with_name("btnPlay")


# Exits to character selection screen if logged in
async def logout(client, tryAgain = True):
    if not await inGame(client): return

    # ValueError is raised if no button found
    try: await client.mouse_handler.click_window_with_name("QuitButton")

    except ValueError:
        await client.send_key(wizwalker.Keycode.ESC)
        await asyncio.sleep(1.0)

        if not tryAgain:
            try: await client.send_key(wizwalker.Keycode.ESC)
            except ValueError: pass
            return

        await logout(client, True)

# Collect mana (one wisp per call)
# Threshold (minimum mana value before function returns)
async def collectMana(client, threshold = -1):
    # Exit if threshold is met
    manaVal = await client.stats.current_mana()
    print(f"Current mana: {manaVal} / {threshold}")
    if threshold > 0 and manaVal >= threshold: return

    # Get a list of wisps
    mana = await client.get_base_entities_with_name("WC_WispMana")

    if len(mana) > 0:
        loc = await mana[0].location()
        print(f"Collecting mana at ({loc.x}, {loc.y}, {loc.z})")
        await client.teleport(loc)

    # If no mana, wait for more to spawn
    else:
        print("No mana found, waiting...")
        await asyncio.sleep(10.0)

    await asyncio.sleep(2.5)
    if threshold < 0: return
    await collectMana(client, threshold)


# Teleport to health wisps
# Currently configured for known safe zones within grand arena
# Returns 0 if threshold is met, 1 if no wisps found (only applies when threshold not set)
async def collectHealth(client, threshold = -1):
    healthVal = await client.stats.current_hitpoints()
    print(f"Current health: {healthVal} / {threshold}")
    if threshold > 0 and healthVal >= threshold: return 0

    # Wisps don't render if we're out of range
    # await client.teleport(wizwalker.utils.XYZ(-6050.0, 29500.0, 0.5))

    # Find a wisp in a safe zone
    wispFound = False
    wisps = await client.get_base_entities_with_name("KT_WispHealth")
    for ent in wisps:
        loc = await ent.location()

        # Old y min: 25800
        if loc.x < -4500.0 and loc.x > -4900.0 and loc.y > 30000.0 and loc.y < 33200.0: wispFound = True      # Check right side coords
        elif loc.x < -7200.0 and loc.x > -7600.0 and loc.y > 30000.0 and loc.y < 33200.0: wispFound = True      # Check left side coords
        if not wispFound: continue

        print(f"Collecting health at ({loc.x}, {loc.y}, {loc.z})")
        await client.teleport(loc)
        await asyncio.sleep(2.5)    # Needs to be at least ~2.5 because it takes this long for the wisp we are collecting to despawn
        break

    # If no mana, wait for more to spawn
    if not wispFound:
        if threshold < 0: return 1
        print("No health found in safe zone, waiting...")
        await client.send_key(wizwalker.Keycode.D, 0.5)     # Anti-AFK in case this takes longer than expected
        await asyncio.sleep(10.0)

    if threshold < 0: return 0
    return await collectHealth(client, threshold)


# Collect health (one wisp per call)
# Threshold (minimum health value before function returns)
# Currently pretty hacky because we're in a safe zone without health wisps
async def waitHealth(client, threshold = -1):
    # Exit if threshold is met
    healthVal = await client.stats.current_hitpoints()
    print(f"Current health: {healthVal} / {threshold}")
    if threshold > 0 and healthVal >= threshold: return

    print("Waiting for health...")
    await asyncio.sleep(12.0)

    if threshold < 0: return
    await waitHealth(client, threshold)

# Currently doesn't work
async def drinkPotion(client, healthThresh = 100, manaThresh = 20):
    healthVal = await client.stats.current_hitpoints()
    manaVal = await client.stats.current_mana()

    if healthVal < healthThresh or manaVal < manaThresh:
        print("Consuming potion")
        await client.mouse_handler.click_window_with_name("sprtElixir1")

        # For current use case only
        if manaVal == (await client.stats.current_mana()):
            print("Warning: Probably out of potions")


# Travel to the oasis, collect mana, and then travel back to the grand arena
# TODO we might need a small wait after each wait for zone change (rather, before each teleport)
async def collectManaOasis(client, threshold = 100):
    # Use ingame hotkey to travel back (easy part)
    while await client.zone_name() != "Krokotopia/KT_Hub":
        print("Attempting to teleport to Krok Hub...")
        await client.send_key(wizwalker.Keycode.END)
        await asyncio.sleep(8.0)

    await collectMana(client, threshold)

    # Travel back
    boatLoc = wizwalker.utils.XYZ(4200.0, 3172.0, 25.8)
    await client.teleport(boatLoc)
    await asyncio.sleep(1.0)

    # Use boat
    while not await client.is_in_npc_range(): await asyncio.sleep(0.5)  # Maybe TODO give up if we wait too long
    while await client.is_in_npc_range():
        await client.send_key(wizwalker.Keycode.X)
        await asyncio.sleep(0.5)
        # Loading screen on success so this exits
    await client.wait_for_zone_change()
    # await asyncio.sleep(1.0)

    # Skip boat
    while await client.is_in_npc_range():
        await client.send_key(wizwalker.Keycode.X)
        await asyncio.sleep(0.5)
        # Loading screen on success so this exits
    await client.wait_for_zone_change()
    # await asyncio.sleep(1.0)

    # Enter krokosphinx
    await client.teleport(wizwalker.utils.XYZ(15250.0, 3925.0, 851.3))
    await client.goto(15750.5, 3925.0)
    await client.wait_for_zone_change()

    # Enter arena
    # await asyncio.sleep(5.0)    # Not sure why we keep getting stuck here
    await client.teleport(wizwalker.utils.XYZ(6750.0, 35.0, 0.0))
    await client.goto(7150.0, 35.0)
    await client.wait_for_zone_change()

# Primary logic loop
# Pass in reference to hooked client (from ClientHanlder.get_new_clients)
async def foulgazeLoop(client, iter = 1):
    avgLoopTime = 0.0
    loopCount = 0
    while loopCount < iter:
        loopCount += 1
        startTime = time.time()
        print(f"\n-- ITERATION {loopCount} / {iter} --")

        # Log in the wizard (assume desired wizard is indicated)
        await login(client, loopCount > 1)
        await asyncio.sleep(2.5)

        # Ensure wizard is in Olde Town (TODO movement automation)
        while await client.zone_name() != "WizardCity/WC_Streets/WC_OldeTown":
            print("Wizard not in Olde Town! Please go there!")
            await asyncio.sleep(5.0)

        # Ensure player is ready for combat
        await collectMana(client, 20)
        await waitHealth(client, 575)    # Call me second because we gain health passively whilst collecting mana

        # Go to dungeon sigil
        # TODO: Fix coordinates hard coded for now
        await client.teleport(wizwalker.utils.XYZ(-9580.0, -5382.0, -2159.25))
        while not await client.is_in_npc_range(): await asyncio.sleep(0.5)  # Maybe TODO give up if we wait too long
        while await client.is_in_npc_range():
            await asyncio.sleep(0.5)
            await client.send_key(wizwalker.Keycode.X)
        await client.wait_for_zone_change()

        # Begin battle
        print("Beginning combat...")
        await client.goto(40.0, -600.0)
        combatHandler = CombatHandler(client)
        combatHandler.target = "Foulgaze"
        combatHandler.spell = "Thunder Snake"
        await combatHandler.wait_for_combat()   # Calls 'handle_combat() loop with all necessary waits'

        # Write data to file
        if combatHandler.combatData is not None:
            print("Writing data to file...")
            with open("data/thundersnake-250_storm-146.dat", "a") as file:
                file.write('[\n\t')
                for i, line in enumerate(combatHandler.combatData):
                    if i > 0: file.write(",\n\t")
                    # file.write(str(line))
                    file.write(json.dumps(line))
                file.write("\n],\n")

        else:
            print("Error this iteration, skipping")
            iter += 1

        # Logout (to leave dungeon quickly)
        await logout(client)
        await asyncio.sleep(1.0)        # Don't loop too quickly

        # Update completion time estimate
        loopTime = time.time() - startTime
        avgLoopTime = avgLoopTime + ((loopTime - avgLoopTime) / loopCount)
        timeEst = (iter - loopCount) * avgLoopTime

        print()
        print("Time this iteration:", time.strftime("%Hh : %Mm : %Ss", time.gmtime(loopTime)))
        print("Average iteration time:", time.strftime("%Hh : %Mm : %Ss", time.gmtime(avgLoopTime)))
        print("Time remaining (estimated):", time.strftime("%Hh : %Mm : %Ss", time.gmtime(timeEst)))

    print("Total elapsed time:", time.strftime("%Hh : %Mm : %Ss", time.gmtime(avgLoopTime * iter)))


# Combat handler target always Itennu Sokwwi
async def itennuLoop(client, iter = 1, spell = None):
    filepath = f"data/krok/{spell.replace(' ', '').lower()}.dat"
    avgLoopTime = 0.0
    loopCount = 0
    while loopCount < iter:
        loopCount += 1
        startTime = time.time()
        print(f"\n-- ITERATION {loopCount} / {iter} --")

        # Log in the wizard (assume desired wizard is indicated)
        await login(client)     # (loop = loopCount > 1)
        await asyncio.sleep(2.5)

        # Ensure wizard is in Grand Arena (TODO movement automation)
        while await client.zone_name() != "Krokotopia/KT_Krokosphinx/KT_Arena":
            print("Wizard not in Grand Arena! Running mana loop!")
            await collectManaOasis(client)
            await asyncio.sleep(1.0)

        # Ensure player is ready for combat
        # Mana is best found in the oasis
        if await client.stats.current_mana() < 25:
            print("Mana below threshold--Refilling from hub")
            await collectManaOasis(client, await client.stats.max_mana())

        # Collect health if player can use it and there are safe orbs
        # If not, continue to fight but only if we are above the safe amount
        await client.teleport(wizwalker.utils.XYZ(-6050.0, 34500.0, 0.5))   # Location to render as many wisps as possible
        await asyncio.sleep(1.0)
        while (await client.stats.current_hitpoints()) < 1000:
            if (await collectHealth(client)) == 1: break
            await asyncio.sleep(0.5)
        await collectHealth(client, 600)

        # Go to dungeon
        assert((await client.stats.current_hitpoints()) > 0)        # This should never be zero so error out if so
        await client.teleport(wizwalker.utils.XYZ(-6026.5, 37085.0, 0.5))
        await client.goto(-6026.5, 37850.0)
        await client.wait_for_zone_change()

        # Begin battle
        print("Beginning combat...")
        await client.teleport(wizwalker.utils.XYZ(3.2, -1000.0, -222.0))
        combatHandler = CombatHandler(client)
        combatHandler.target = "Itennu Sokkwi"
        # combatHandler.target = "Sand Stalker"
        combatHandler.spell = spell
        await combatHandler.wait_for_combat()   # Calls 'handle_combat() loop with all necessary waits'

        # Write data to file
        if combatHandler.combatData is not None:
            print("Writing data to file...")
            with open(filepath, "a") as file:
                file.write('[\n\t')
                for i, line in enumerate(combatHandler.combatData):
                    if i > 0: file.write(",\n\t")
                    # file.write(str(line))
                    file.write(json.dumps(line))
                file.write("\n],\n")

        else:
            print("Error this iteration, skipping")
            iter += 1

        # Logout (to leave dungeon quickly)
        await logout(client)
        await asyncio.sleep(1.0)        # Don't loop too quickly

        # Update completion time estimate
        loopTime = time.time() - startTime
        avgLoopTime = avgLoopTime + ((loopTime - avgLoopTime) / loopCount)
        timeEst = (iter - loopCount) * avgLoopTime

        print()
        print("Time this iteration:", time.strftime("%Hh : %Mm : %Ss", time.gmtime(loopTime)))
        print("Average iteration time:", time.strftime("%Hh : %Mm : %Ss", time.gmtime(avgLoopTime)))
        print("Time remaining (estimated):", time.strftime("%Hh : %Mm : %Ss", time.gmtime(timeEst)))

    print("Total elapsed time:", time.strftime("%Hh : %Mm : %Ss", time.gmtime(avgLoopTime * iter)))


# TODO handle unrecognized argument
async def main():
    if '-h' in sys.argv or '--help' in sys.argv:
        print(
        f"Usage: {sys.argv[0]} [options]\n"                                     + \
        "Options:\n"                                                            + \
        "\t--help (-h)   : Print this help and exit\n"                          + \
        "\t--login (-l)  : Create a new instance of Wizard101 before launch\n"  + \
        "\t--patch (-p)  : Patch out opening the browser upon game close\n"     + \
        "\t                (Reset everytime game is launched via launcher)\n"   + \
        "\t ======================= DEBUG OPTIONS =========================\n"  + \
        "\t--position    : Print client position\n"                             + \
        "\t--zone        : Print client zone name\n"                            + \
        "\t--entities    : Print all of the entities currently rendered\n"      + \
        "\t--ui          : Print full UI tree\n"                                + \
        "\t--mouse       : Attempt to deactivate mouseless mode\n"              + \
        "\t               (Useful during crashes when mouse is still hooked)"   )
        exit(0)

    # Start the client if necessary
    if '-l' in sys.argv or '--login' in sys.argv:
        await wizwalker.utils.start_instances_with_login(1, ["Xenoderg:kD$eoWR*Q3I9gXqRCZ2$"])

    if '-p' in sys.argv or '--patch' in sys.argv:
        wizwalker.utils.patch_open_browser()

    # Hook the client
    handler = wizwalker.ClientHandler()
    client = handler.get_new_clients()[0]

    try:
        print("Hooking client...")
        await client.activate_hooks()

        # Print client position
        debug = False
        if '--position' in sys.argv:
            print("Debug mode: getting position")
            print(await client.body.position())
            debug = True

        # Print client zone name
        if '--zone' in sys.argv:
            print("Debug mode: getting zone name")
            print(await client.zone_name())
            debug = True

        if '--entities' in sys.argv:
            print("Debug mode: getting entity list")
            entities = await client.get_base_entity_list()
            print("-- ENTITIES --")
            print("Object Name\t|  Display Name\t |  Position")
            for e in entities:
                print(f"{await e.object_name()},\t{await e.display_name()},\t{await e.location()}")
            debug = True

        # Print the UI tree
        if '--ui' in sys.argv:
            print("Debug mode: getting UI tree")
            await client.root_window.debug_print_ui_tree()
            debug = True

        # Attempt to unhook mouseless mode onbehalf of the bot crashing during testing
        if '--mouse' in sys.argv:
            print("Debug mode: Attempting to deactivate mouseless mode")
            try:
                await client.mouse_handler.deactivate_mouseless()
                print("Successfully deactivated mouseless mode")
            except Exception: pass
            debug = True

        if debug: exit(0)

        print("Welcome to Wizard101 spell data collection utility!")
        await client.mouse_handler.activate_mouseless()

        # Could be less hacky, but once the client is hooked we need to start from here thanks to funny loading screen problems
        await logout(client)

        # await itennuLoop(client, 10, "Fire Cat")
        # await itennuLoop(client, 10, "Frost Beetle")
        await itennuLoop(client, 133, "Thunder Snake")        # After collecting, rename base to 'thundersnake-boss.dat'
        # await itennuLoop(client, 160, "Dark Sprite")       # Don't forget to normalize shield and non-shield case
        # await itennuLoop(client, 367, "Imp")               # Also needs res normalization
        # await itennuLoop(client, 294, "Bloodbat")
        # await itennuLoop(client, 242, "Scarab")

        print("\nData collection finished!")
        await client.mouse_handler.deactivate_mouseless()

    except Exception as e: print(e)

    finally:
        print("Unhooking client...")
        await handler.close()


if __name__ == "__main__":
    asyncio.run(main())
