################################################################################
###                                                                          ###
### Created by Mahdi Manoochhertaybei, 2020-2023                             ###
###                                                                          ###
### École Polytechnique, Palaiseau, France                                   ###
###                                                                          ###
### And Martin Genet, 2020-2023                                              ###
###                                                                          ###
### École Polytechnique, Palaiseau, France                                   ###
###                                                                          ###
################################################################################

import meshio
import gmsh
import os
import dolfin

################################################################################

def generate_mesh_porous_square(mesh_filename, width, r, shift_x, shift_y):


    ########### Initialization #################################################

    center = width/2
    xmin = 0.
    ymin = 0.
    zmin = 0.
    xmax = width
    ymax = width
    zmax = width
    r0 = r
    l = width/50 
    e = 1e-6


    def setPeriodic(coord):
        # From https://gitlab.onelab.info/gmsh/gmsh/-/issues/744
        smin = gmsh.model.getEntitiesInBoundingBox(xmin - e, ymin - e, zmin - e,
                                                    (xmin + e) if (coord == 0) else (xmax + e),
                                                    (ymin + e) if (coord == 1) else (ymax + e),
                                                    (zmin + e) if (coord == 2) else (zmax + e),
                                                    2)
        dx = (xmax - xmin) if (coord == 0) else 0
        dy = (ymax - ymin) if (coord == 1) else 0
        dz = (zmax - zmin) if (coord == 2) else 0

        for i in smin:
            bb = gmsh.model.getBoundingBox(i[0], i[1])
            bbe = [bb[0] - e + dx, bb[1] - e + dy, bb[2] - e + dz,
                    bb[3] + e + dx, bb[4] + e + dy, bb[5] + e + dz]
            smax = gmsh.model.getEntitiesInBoundingBox(bbe[0], bbe[1], bbe[2],
                                                        bbe[3], bbe[4], bbe[5])
            for j in smax:
                bb2 = list(gmsh.model.getBoundingBox(j[0], j[1]))
                bb2[0] -= dx; bb2[1] -= dy; bb2[2] -= dz;
                bb2[3] -= dx; bb2[4] -= dy; bb2[5] -= dz;
                if ((abs(bb2[0] - bb[0]) < e) and (abs(bb2[1] - bb[1]) < e) and
                    (abs(bb2[2] - bb[2]) < e) and (abs(bb2[3] - bb[3]) < e) and
                    (abs(bb2[4] - bb[4]) < e) and (abs(bb2[5] - bb[5]) < e)):
                    gmsh.model.mesh.setPeriodic(2, [j[1]], [i[1]], [1, 0, 0, dx,\
                                                                    0, 1, 0, dy,\
                                                                    0, 0, 1, dz,\
                                                                    0, 0, 0, 1 ])

    gmsh.initialize()

    box_tag = 1
    hole_tag2 = 2
    hole_tag3 = 3
    hole_tag4 = 4
    hole_tag5 = 5
    rve_tag = 6

    gmsh.model.occ.addRectangle(x=xmin+shift_x, y=ymin+shift_y, z=0, dx=xmax-xmin, dy=ymax-ymin, tag=box_tag)
    gmsh.model.occ.addDisk(xc=xmin, yc=ymin, zc=0, rx=r0, ry=r0, tag=hole_tag2)
    gmsh.model.occ.addDisk(xc=xmax, yc=ymin, zc=0, rx=r0, ry=r0, tag=hole_tag3)
    gmsh.model.occ.addDisk(xc=xmax, yc=ymax, zc=0, rx=r0, ry=r0, tag=hole_tag4)
    gmsh.model.occ.addDisk(xc=xmin, yc=ymax, zc=0, rx=r0, ry=r0, tag=hole_tag5)
    gmsh.model.occ.cut(objectDimTags=[(2, box_tag)], toolDimTags=[(2, hole_tag2), (2, hole_tag3), (2, hole_tag4), (2, hole_tag5)], tag=rve_tag)
    gmsh.model.occ.synchronize()
    gmsh.model.addPhysicalGroup(dim=2, tags=[rve_tag])

    
    setPeriodic(0)
    setPeriodic(1)
    gmsh.model.mesh.setSize(dimTags=gmsh.model.getEntities(0), size=l)
    gmsh.model.mesh.generate(dim=2)


    gmsh.write(mesh_filename + '.msh')
    os.system("gmsh -2 -o " + mesh_filename + ".msh -format msh22 " + mesh_filename + ".msh")
    os.system("dolfin-convert " + mesh_filename + ".msh " +  mesh_filename + ".xml")

    gmsh.write(mesh_filename+"-mesh.vtk")
    gmsh.finalize()

    mesh = meshio.read(mesh_filename+"-mesh.vtk")
    mesh.points = mesh.points[:, :2]
    meshio.write(mesh_filename+"-mesh.xdmf", mesh)

    mesh = dolfin.Mesh()
    dolfin.XDMFFile(mesh_filename+"-mesh.xdmf").read(mesh)
    coord = mesh.coordinates()
    xmax = max(coord[:,0]); xmin = min(coord[:,0])
    ymax = max(coord[:,1]); ymin = min(coord[:,1])
    vol = (xmax - xmin)*(ymax - ymin)
    dV = dolfin.Measure("dx",domain=mesh)
    Vs0 = dolfin.assemble(dolfin.Constant(1) * dV)

    phi = (vol - Vs0)/vol
    print("porosity:" +str(phi))
