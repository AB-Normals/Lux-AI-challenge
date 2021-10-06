#ifndef map_h
#define map_h
#include <vector>
#include "city.hpp"
#include "position.hpp"
namespace lux
{
    using namespace std;
    enum ResourceType
    {
        wood = 'w',
        coal = 'c',
        uranium = 'u'
    };
    class Resource
    {
    public:
        ResourceType type;
        int amount = -1;
    };
    class Cell
    {
    public:
        Position pos = Position(-1, -1);
        Resource resource;
        lux::CityTile * citytile;
        float road = 0.0;
        Cell(){};
        Cell(int x, int y)
        {
            pos = Position(x, y);
        };
        bool hasResource() const
        {
            return this->resource.amount > 0;
        }
    };
    class GameMap
    {
    public:
        int width = -1;
        int height = -1;
        vector<vector<Cell>> map;
        GameMap(){};
        GameMap(int width, int height) : width(width), height(height)
        {
            map = vector<vector<Cell>>(height, vector<Cell>(width));
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    map[y][x] = Cell(x, y);
                }
            }
        };
        Cell const *getCellByPos(const Position &pos) const
        {
            return &map[pos.y][pos.x];
        }
        Cell const *getCell(int x, int y) const
        {
            return &map[y][x];
        }
        Cell *getCellByPos(const Position &pos)
        {
            return &map[pos.y][pos.x];
        }
        Cell *getCell(int x, int y)
        {
            return &map[y][x];
        }
        void _setResource(const ResourceType &type, int x, int y, int amount)
        {
            Cell *cell = getCell(x, y);
            cell->resource = Resource();
            cell->resource.amount = amount;
            cell->resource.type = type;
        }
    };

};
#endif
