#ifndef game_objects_h
#define game_objects_h
#include <vector>
#include "map.hpp"
#include "position.hpp"
#include "constants.hpp"
namespace lux
{
    using namespace std;
    class Cargo
    {
    public:
        int wood = 0;
        int coal = 0;
        int uranium = 0;
        Cargo(){};
    };
    class Unit
    {
    public:
        lux::Position pos;
        int team;
        string id;
        int type;
        int cooldown;
        Cargo cargo;
        Unit(){};
        Unit(int teamid, int type, const string &unitid, int x, int y, int cooldown, int wood, int coal, int uranium)
        {
            this->pos = lux::Position(x, y);
            this->team = teamid;
            this->id = unitid;
            this->type = type;
            this->cooldown = cooldown;
            this->cargo.wood = wood;
            this->cargo.coal = coal;
            this->cargo.uranium = uranium;
        };
        bool isWorker() const
        {
            return this->type == 0;
        }
        bool isCart() const
        {
            return this->type == 1;
        }
        int getCargoSpaceLeft() const
        {
            int spaceused = this->cargo.wood + this->cargo.coal + this->cargo.uranium;
            if (this->type == 0)
            {
                return (int)GAME_CONSTANTS["PARAMETERS"]["RESOURCE_CAPACITY"]["WORKER"] - spaceused;
            }
            else
            {
                return (int)GAME_CONSTANTS["PARAMETERS"]["RESOURCE_CAPACITY"]["CART"] - spaceused;
            }
        }

        /** whether or not the unit can act or not */
        bool canAct() const
        {
            return this->cooldown < 1;
        }

        /** whether or not the unit can build where it is right now */
        bool canBuild(const GameMap &gameMap) const
        {
            auto cell = gameMap.getCellByPos(this->pos);
            if (!cell->hasResource() && this->canAct() && (this->cargo.wood + this->cargo.coal + this->cargo.uranium) >= GAME_CONSTANTS["PARAMETERS"]["CITY_BUILD_COST"])
            {
                return true;
            }
            return false;
        }

        /** return the command to move unit in the given direction */
        string move(const DIRECTIONS &dir) const
        {
            return "m " + this->id + " " + (char)dir;
        }

        /** return the command to transfer a resource from a source unit to a destination unit as specified by their ids or the units themselves */
        string transfer(const string &src_unit_id, const string &dest_unit_id, const ResourceType &resourceType, int amount) const
        {
            string resourceName;
            switch (resourceType)
            {
            case ResourceType::wood:
                resourceName = "wood";
                break;
            case ResourceType::coal:
                resourceName = "coal";
                break;
            case ResourceType::uranium:
                resourceName = "uranium";
                break;
            }
            return "t " + src_unit_id + " " + dest_unit_id + " " + resourceName + " " + to_string(amount);
        }
        /** return the command to build a city right under the worker */
        string buildCity() const
        {
            return "bcity " + this->id;
        }

        /** return the command to pillage whatever is underneath the worker */
        string pillage() const
        {
            return "p " + this->id;
        }
    };
    class Player
    {
    public:
        int researchPoints = 0;
        int team = -1;
        vector<Unit> units{};
        map<string, City> cities{};
        int cityTileCount = 0;
        Player(){};
        Player(int team_id) : team(team_id) {}
        bool researchedCoal()
        {
            return this->researchPoints >= (int)GAME_CONSTANTS["PARAMETERS"]["RESEARCH_REQUIREMENTS"]["COAL"];
        }
        bool researchedUranium()
        {
            return this->researchPoints >= (int)GAME_CONSTANTS["PARAMETERS"]["RESEARCH_REQUIREMENTS"]["URANIUM"];
        }
    };
};
#endif
