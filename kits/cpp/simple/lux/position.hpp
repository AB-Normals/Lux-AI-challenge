#ifndef position_h
#define position_h
#include <vector>
#include <string>
#include "constants.hpp"
namespace lux
{
    using namespace std;
    class Position
    {
    public:
        int x = -1;
        int y = -1;
        Position() {}
        Position(int x, int y)
        {
            this->x = x;
            this->y = y;
        }
        bool isAdjacent(const Position &pos)
        {
            const int dx = this->x - pos.x;
            const int dy = this->y - pos.y;
            if (abs(dx) + abs(dy) > 1)
            {
                return false;
            }
            return true;
        }
        bool operator==(const Position &pos)
        {
            return this->x == pos.x && this->y == pos.y;
        }
        bool operator!=(const Position &pos)
        {
            return !(operator==(pos));
        }

        Position translate(const DIRECTIONS &direction, int units)
        {
            switch (direction)
            {
            case DIRECTIONS::NORTH:
                return Position(this->x, this->y - units);
            case DIRECTIONS::EAST:
                return Position(this->x + units, this->y);
            case DIRECTIONS::SOUTH:
                return Position(this->x, this->y + units);
            case DIRECTIONS::WEST:
                return Position(this->x - units, this->y);
            case DIRECTIONS::CENTER:
                return Position(this->x, this->y);
            }
        }

        /** Returns Manhattan distance to pos from this position */
        float distanceTo(const Position &pos) const
        {
            return abs(pos.x - this->x) + abs(pos.y - this->y);
        }

        /** Returns closest direction to targetPos, or center if staying put is best */
        DIRECTIONS directionTo(const Position &targetPos)
        {

            DIRECTIONS closestDirection = DIRECTIONS::CENTER;
            float closestDist = this->distanceTo(targetPos);
            for (const DIRECTIONS dir : ALL_DIRECTIONS)
            {
                const Position newpos = this->translate(dir, 1);
                float dist = targetPos.distanceTo(newpos);
                if (dist < closestDist)
                {
                    closestDist = dist;
                    closestDirection = dir;
                }
            }
            return closestDirection;
        }
        friend ostream &operator<<(ostream &out, const Position &p);
        operator std::string() const
        {
            return "(" + to_string(this->x) + ", " + to_string(this->y) + ")";
        }
    };
    ostream &operator<<(ostream &out, const Position &p);
}

#endif
