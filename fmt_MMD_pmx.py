#By Minmode

from inc_noesis import *
import noesis
import rapi
import math

anim2morph = False
frameSplit = 100

def registerNoesisTypes():
      handle = noesis.register("MMD Model", ".pmx")
      noesis.setHandlerWriteModel(handle, pmxWriteModel)
      handle = noesis.register("MMD Animation", ".vmd")
      noesis.setHandlerWriteAnim(handle, vmdWriteAnim)
      return 1

def pmxWriteModel(mdl, bs):
      bs.writeBytes("PMX ".encode())#magic
      bs.writeFloat(2.0)#version

      bs.writeByte(8)#data count
      bs.writeByte(0)#encoding 0 UTF16, 1 UTF8
      bs.writeByte(4)#adduv 

      texList = []
      matList = {}
      if mdl.modelMats:
            for mat in mdl.modelMats.matList:
                  matList[mat.name] = mat
                  if mat.texName not in texList:
                        texList.append(mat.texName)
                  if hasattr(mat, "envTexName") and mat.envTexName not in texList:
                        texList.append(mat.envTexName)

      morphCount = 0
      for mesh in mdl.meshes:
            morphCount += len(mesh.morphList)
      if anim2morph:
            animMorphs = []
            anims = rapi.getDeferredAnims()
            for anim in anims:
                  frameCount = anim.numFrames
                  if frameCount >= frameSplit * 2:
                        count = 0
                        subCount = 0
                        for i in range(0, frameCount):
                              if ((i + 1) % frameSplit == 0) and i != 0:
                                    animData = []
                                    for a in range(0, len(anim.bones)):
                                          matrix = anim.bones[a]._matrix * anim.bones[anim.bones[a].parentIndex]._matrix.inverse()
                                          if anim.bones[a].parentIndex != -1:
                                                posX = anim.frameMats[count][3][0] - matrix[3][0]
                                                posY = anim.frameMats[count][3][1] - matrix[3][1]
                                                posZ = anim.frameMats[count][3][2] - matrix[3][2]
                                          else:
                                                posX = anim.frameMats[count][3][0] - anim.bones[a]._matrix[3][0]
                                                posY = anim.frameMats[count][3][1] - anim.bones[a]._matrix[3][1]
                                                posZ = anim.frameMats[count][3][2] - anim.bones[a]._matrix[3][2]
                                          bm = anim.bones[a]._matrix.toQuat()
                                          if anim.bones[a].parentIndex != -1:
                                                pbm = anim.bones[anim.bones[a].parentIndex]._matrix.toQuat()
                                                quat = anim.frameMats[count].toQuat() * pbm
                                          else:
                                                quat = anim.frameMats[count].toQuat()
                                          bm[0] *= -1
                                          bm[1] *= -1
                                          bm[3] *= -1
                                          quat[0] *= -1
                                          quat[1] *= -1
                                          quat[3] *= -1
                                          quat = (quat.toMat43() * bm.toMat43().inverse()).toQuat()
                                          count += 1
                                          if [posX, posY, posZ] != [0.0, 0.0, 0.0] or quat != NoeQuat():
                                                animData.append([anim.bones[a].index - 1, posX, posY, posZ, quat])
                                    animMorphs.append([anim.name + "_morph" + str(subCount), animData])
                                    subCount += 1
                              else:
                                    count += len(anim.bones)
                  else:
                        count = 0
                        for i in range(0, frameCount):
                              if ((i + 1) % frameSplit == 0) and i != 0:
                                    animData = []
                                    for a in range(0, len(anim.bones)):
                                          matrix = anim.bones[a]._matrix * anim.bones[anim.bones[a].parentIndex]._matrix.inverse()
                                          if anim.bones[a].parentIndex != -1:
                                                posX = anim.frameMats[count][3][0] - matrix[3][0]
                                                posY = anim.frameMats[count][3][1] - matrix[3][1]
                                                posZ = anim.frameMats[count][3][2] - matrix[3][2]
                                          else:
                                                posX = anim.frameMats[count][3][0] - anim.bones[a]._matrix[3][0]
                                                posY = anim.frameMats[count][3][1] - anim.bones[a]._matrix[3][1]
                                                posZ = anim.frameMats[count][3][2] - anim.bones[a]._matrix[3][2]
                                          bm = anim.bones[a]._matrix.toQuat()
                                          quat = anim.frameMats[count].toQuat()
                                          if anim.bones[a].parentIndex != -1:
                                                pbm = anim.bones[anim.bones[a].parentIndex]._matrix.toQuat()
                                                quat *= pbm
                                          bm[0] *= -1
                                          bm[1] *= -1
                                          bm[3] *= -1
                                          quat[0] *= -1
                                          quat[1] *= -1
                                          quat[3] *= -1
                                          quat = (quat.toMat43() * bm.toMat43().inverse()).toQuat()
                                          count += 1
                                          if [posX, posY, posZ] != [0.0, 0.0, 0.0] or quat != NoeQuat():
                                                animData.append([anim.bones[a].index, posX, posY, posZ, quat])
                                    animMorphs.append([anim.name, animData])
                              else:
                                    count += len(anim.bones)
            morphCount += len(animMorphs)
      
      vertIdxSize = getIndexSize(len(mdl.globalVtx), 1)
      bs.writeByte(vertIdxSize)
      texIdxSize = getIndexSize(len(texList), 0)
      bs.writeByte(texIdxSize)#texture index size
      matIdxSize = getIndexSize(len(mdl.meshes), 0)
      bs.writeByte(matIdxSize)#material index size
      boneIdxSize = getIndexSize(len(mdl.bones), 0)
      bs.writeByte(boneIdxSize)#bone index size
      morphIdxSize = getIndexSize(morphCount, 0)
      bs.writeByte(morphIdxSize)#morph index size
      bs.writeByte(1)#rigid index size

      fileName = rapi.getExtensionlessName(rapi.getLocalFileName(rapi.getLastCheckedName()))
      bs.writeInt(len(fileName) * 2)#jp name length
      bs.writeBytes(fileName.encode("utf-16-le"))#jp name
      bs.writeInt(len(fileName) * 2)#en name length
      bs.writeBytes(fileName.encode("utf-16-le"))#en name
      bs.writeInt(0)#jp comment length
      bs.writeInt(0)#en comment length

      colIsInt = False
      for mesh in mdl.meshes:
            if len(mesh.colors) != 0:
                  for i in range (0, len(mesh.positions)):
                        if mesh.colors[i][3] > 1.0:
                              colIsInt = True
                              break

      bs.writeInt(len(mdl.globalVtx))#vertex count
      for mesh in mdl.meshes:
            for i in range (0, len(mesh.positions)):
                  bs.writeFloat(mesh.positions[i][0])#positon
                  bs.writeFloat(mesh.positions[i][1])
                  bs.writeFloat(mesh.positions[i][2] * -1)
                  bs.writeFloat(mesh.normals[i][0])#normal
                  bs.writeFloat(mesh.normals[i][1])
                  bs.writeFloat(mesh.normals[i][2] * -1)
                  bs.writeFloat(mesh.uvs[i][0])#uv
                  bs.writeFloat(mesh.uvs[i][1])#uv
                  if len(mesh.lmUVs) != 0:
                        bs.writeFloat(mesh.lmUVs[i][0])#adduv1
                        bs.writeFloat(mesh.lmUVs[i][1])
                  else:
                        bs.writeFloat(0.0)
                        bs.writeFloat(0.0)
                  if len(mesh.uvxList) >= 1:
                        bs.writeFloat(mesh.uvxList[0][i][0])#adduv1
                        bs.writeFloat(mesh.uvxList[0][i][1])
                  else:
                        bs.writeFloat(0.0)
                        bs.writeFloat(0.0)
                  if len(mesh.colors) != 0:
                        if colIsInt:
                              bs.writeFloat(mesh.colors[i][0] / 255)
                              bs.writeFloat(mesh.colors[i][1] / 255)
                              bs.writeFloat(mesh.colors[i][2] / 255)
                              bs.writeFloat(mesh.colors[i][3] / 255)
                        else:
                              bs.writeBytes(mesh.colors[i].toBytes())#adduv2
                  else:
                        bs.writeFloat(1.0)
                        bs.writeFloat(1.0)
                        bs.writeFloat(1.0)
                        bs.writeFloat(1.0)
                  bs.writeFloat(mesh.tangents[i][2][0])
                  bs.writeFloat(mesh.tangents[i][2][1])
                  bs.writeFloat(mesh.tangents[i][2][2] * -1)
                  w = (mesh.tangents[i][0][1] * mesh.tangents[i][2][2]) - (mesh.tangents[i][0][2] * mesh.tangents[i][2][1])
                  if w >= 0.0 and mesh.tangents[i][1][0] >= 0.0:
                        bs.writeFloat(1.0)
                  elif w <= 0.0 and mesh.tangents[i][1][0] <= 0.0:
                        bs.writeFloat(1.0)
                  else:
                        bs.writeFloat(-1.0)
                  if len(mesh.uvxList) >= 2:
                        bs.writeFloat(mesh.uvxList[1][i][0])#adduv4
                        bs.writeFloat(mesh.uvxList[1][i][1])
                  else:
                        bs.writeFloat(0.0)
                        bs.writeFloat(0.0)
                  if len(mesh.uvxList) >= 3:
                        bs.writeFloat(mesh.uvxList[2][i][0])#adduv4
                        bs.writeFloat(mesh.uvxList[2][i][1])
                  else:
                        bs.writeFloat(0.0)
                        bs.writeFloat(0.0)
                  if len(mesh.weights) != 0:
                        weightNum = mesh.weights[i].numWeights()
                        if weightNum == 1:
                              bs.writeByte(0)#weight type
                              if boneIdxSize == 1:
                                    bs.writeByte(mesh.weights[i].indices[0])
                              elif boneIdxSize == 2:
                                    bs.writeShort(mesh.weights[i].indices[0])
                              elif boneIdxSize == 4:
                                    bs.writeInt(mesh.weights[i].indices[0])
                        elif weightNum == 2:
                              bs.writeByte(1)
                              if boneIdxSize == 1:
                                    bs.writeByte(mesh.weights[i].indices[0])
                                    bs.writeByte(mesh.weights[i].indices[1])
                              elif boneIdxSize == 2:
                                    bs.writeShort(mesh.weights[i].indices[0])
                                    bs.writeShort(mesh.weights[i].indices[1])
                              elif boneIdxSize == 4:
                                    bs.writeInt(mesh.weights[i].indices[0])
                                    bs.writeInt(mesh.weights[i].indices[1])
                              bs.writeFloat(mesh.weights[i].weights[0])
                        elif weightNum == 3:
                              bs.writeByte(2)
                              if boneIdxSize == 1:
                                    bs.writeByte(mesh.weights[i].indices[0])
                                    bs.writeByte(mesh.weights[i].indices[1])
                                    bs.writeByte(mesh.weights[i].indices[2])
                                    bs.writeByte(0)
                              elif boneIdxSize == 2:
                                    bs.writeShort(mesh.weights[i].indices[0])
                                    bs.writeShort(mesh.weights[i].indices[1])
                                    bs.writeShort(mesh.weights[i].indices[2])
                                    bs.writeShort(0)
                              elif boneIdxSize == 4:
                                    bs.writeInt(mesh.weights[i].indices[0])
                                    bs.writeInt(mesh.weights[i].indices[1])
                                    bs.writeInt(mesh.weights[i].indices[2])
                                    bs.writeInt(0)
                              bs.writeFloat(mesh.weights[i].weights[0])
                              bs.writeFloat(mesh.weights[i].weights[1])
                              bs.writeFloat(mesh.weights[i].weights[2])
                              bs.writeFloat(0.0)
                        elif weightNum == 4:
                              bs.writeByte(2)
                              if boneIdxSize == 1:
                                    bs.writeByte(mesh.weights[i].indices[0])
                                    bs.writeByte(mesh.weights[i].indices[1])
                                    bs.writeByte(mesh.weights[i].indices[2])
                                    bs.writeByte(mesh.weights[i].indices[3])
                              elif boneIdxSize == 2:
                                    bs.writeShort(mesh.weights[i].indices[0])
                                    bs.writeShort(mesh.weights[i].indices[1])
                                    bs.writeShort(mesh.weights[i].indices[2])
                                    bs.writeShort(mesh.weights[i].indices[3])
                              elif boneIdxSize == 4:
                                    bs.writeInt(mesh.weights[i].indices[0])
                                    bs.writeInt(mesh.weights[i].indices[1])
                                    bs.writeInt(mesh.weights[i].indices[2])
                                    bs.writeInt(mesh.weights[i].indices[3])
                              bs.writeFloat(mesh.weights[i].weights[0])
                              bs.writeFloat(mesh.weights[i].weights[1])
                              bs.writeFloat(mesh.weights[i].weights[2])
                              bs.writeFloat(mesh.weights[i].weights[3])
                        else:
                              bs.writeByte(2)
                              sortedList = sorted(zip(mesh.weights[i].weights, mesh.weights[i].indices), reverse=True)
                              indices = [x for _,x in sortedList]
                              weights = [x for x,_ in sortedList]
                              if boneIdxSize == 1:
                                    bs.writeByte(indices[0])
                                    bs.writeByte(indices[1])
                                    bs.writeByte(indices[2])
                                    bs.writeByte(indices[3])
                              elif boneIdxSize == 2:
                                    bs.writeShort(indices[0])
                                    bs.writeShort(indices[1])
                                    bs.writeShort(indices[2])
                                    bs.writeShort(indices[3])
                              elif boneIdxSize == 4:
                                    bs.writeInt(indices[0])
                                    bs.writeInt(indices[1])
                                    bs.writeInt(indices[2])
                                    bs.writeInt(indices[3])
                              totalWeights = weights[0] + weights[1] + weights[2] + weights[3]
                              bs.writeFloat(weights[0] / totalWeights)
                              bs.writeFloat(weights[1] / totalWeights)
                              bs.writeFloat(weights[2] / totalWeights)
                              bs.writeFloat(weights[3] / totalWeights)
                  else:
                        bs.writeByte(0)
                        if boneIdxSize == 1:
                              bs.writeByte(0)
                        elif boneIdxSize == 2:
                              bs.writeShort(0)
                        elif boneIdxSize == 4:
                              bs.writeInt(0)
                  bs.writeFloat(1.0)#edge scale

      bs.writeInt(len(mdl.globalIdx))#face count
      total = 0
      for mesh in mdl.meshes:
            for i in range(0, int(len(mesh.indices) / 3)):
                  if vertIdxSize == 1:
                        bs.writeUByte(mesh.indices[i * 3] + total)
                        bs.writeUByte(mesh.indices[i * 3 + 2] + total)
                        bs.writeUByte(mesh.indices[i * 3 + 1] + total)
                  elif vertIdxSize == 2:
                        bs.writeUShort(mesh.indices[i * 3 ] + total)
                        bs.writeUShort(mesh.indices[i * 3 + 2] + total)
                        bs.writeUShort(mesh.indices[i * 3 + 1] + total)
                  elif vertIdxSize == 4:
                        bs.writeInt(mesh.indices[i * 3] + total)
                        bs.writeInt(mesh.indices[i * 3 + 2] + total)
                        bs.writeInt(mesh.indices[i * 3 + 1] + total)
            total += len(mesh.positions)

      bs.writeInt(len(texList))#texture count
      for i in range(0, len(texList)):
            texList[i] = texList[i].replace('\\\\', '\\')
            bs.writeInt((len(texList[i])) * 2)#jp name length
            bs.writeBytes((texList[i]).encode("utf-16-le"))#jp name

      bs.writeInt(len(mdl.meshes))#material count
      fix = False
      if mdl.meshes[0].name.startswith("0000_"):
            fix = True
      for mesh in mdl.meshes:
            if mesh.matName in matList:
                  mat = matList[mesh.matName]
                  bs.writeInt(len(mat.name) * 2)#jp name length
                  bs.writeBytes(mat.name.encode("utf-16-le"))#jp name
                  bs.writeInt(len(mat.name) * 2)#en name length
                  bs.writeBytes(mat.name.encode("utf-16-le"))#en name
                  bs.writeBytes(mat.diffuseColor.toBytes())#diffuse colour
                  bs.writeBytes(mat.specularColor.toBytes())#specular colour
                  bs.writeFloat(mat.ambientColor[0])#ambient colour
                  bs.writeFloat(mat.ambientColor[1])
                  bs.writeFloat(mat.ambientColor[2])
                  bs.writeByte(14)
                  bs.writeFloat(0.0)
                  bs.writeFloat(0.0)
                  bs.writeFloat(0.0)
                  bs.writeFloat(1.0)
                  bs.writeFloat(1.0)
                  bs.writeByte(texList.index(mat.texName.replace('\\\\', '\\')))
                  # if hasattr(mat, "envTexName"):
                  #       bs.writeByte(texList.index(mat.envTexName))
                  #       bs.writeByte(2)
                  # else:
                  bs.writeByte(-1)
                  bs.writeByte(0)
                  bs.writeByte(1)
                  bs.writeByte(0)
                  if fix:
                        memo = mesh.name[5:]
                  else:
                        memo = mesh.name
                  if hasattr(mat, "nrmTexName"):
                        memo += "\r\nNormal map: " + mat.nrmTexName
                  if hasattr(mat, "specTexName"):
                        memo += "\r\nSpecular map: " + mat.specTexName
                  # if hasattr(mat, "envTexName"):
                  #       memo += "\r\nEnvironment map: " + mat.envTexName
                  if hasattr(mat, "occlTexName"):
                        memo += "\r\nAmbient occlusion map: " + mat.occlTexName
                  bs.writeInt(len(memo) * 2)
                  bs.writeBytes(memo.encode("utf-16-le"))
                  bs.writeInt(len(mesh.indices))
            else:
                  bs.writeInt(len(mesh.name[5:]) * 2)#jp name length
                  bs.writeBytes(mesh.name[5:].encode("utf-16-le"))#jp name
                  bs.writeInt(len(mesh.name[5:]) * 2)#en name length
                  bs.writeBytes(mesh.name[5:].encode("utf-16-le"))#en name
                  bs.writeFloat(1.0)#diffuse colour
                  bs.writeFloat(1.0)
                  bs.writeFloat(1.0)
                  bs.writeFloat(1.0)
                  bs.writeFloat(0.0)#specular colour
                  bs.writeFloat(0.0)
                  bs.writeFloat(0.0)
                  bs.writeFloat(32.0)
                  bs.writeFloat(0.5)#ambient colour
                  bs.writeFloat(0.5)
                  bs.writeFloat(0.5)
                  bs.writeByte(14)
                  bs.writeFloat(0.0)
                  bs.writeFloat(0.0)
                  bs.writeFloat(0.0)
                  bs.writeFloat(1.0)
                  bs.writeFloat(1.0)
                  bs.writeByte(-1)
                  bs.writeByte(-1)
                  bs.writeByte(0)
                  bs.writeByte(1)
                  bs.writeByte(0)
                  bs.writeInt(len(mesh.name) * 2)
                  bs.writeBytes(mesh.name.encode("utf-16-le"))
                  bs.writeInt(len(mesh.indices))

      if len(mdl.bones) != 0:
            bs.writeInt(len(mdl.bones))#bone count
            for bone in mdl.bones:
                  bs.writeInt(len(bone.name) * 2)#jp name length
                  bs.writeBytes(bone.name.encode("utf-16-le"))#jp name
                  bs.writeInt(len(bone.name) * 2)#en name length
                  bs.writeBytes(bone.name.encode("utf-16-le"))#en name
                  bs.writeFloat(bone._matrix[3][0])#transform
                  bs.writeFloat(bone._matrix[3][1])
                  bs.writeFloat(bone._matrix[3][2] * -1)
                  if boneIdxSize == 1:#parent
                        bs.writeByte(bone.parentIndex)
                  elif boneIdxSize == 2:
                        bs.writeShort(bone.parentIndex)
                  elif boneIdxSize == 4:
                        bs.writeInt(bone.parentIndex)
                  bs.writeInt(0)#deform level
                  bs.writeShort(0X081A)#bone flag
                  bs.writeFloat(0.0)
                  bs.writeFloat(0.0)
                  bs.writeFloat(0.0)
                  bm = bone._matrix.toQuat()
                  bm[0] *= -1
                  bm[1] *= -1
                  bm[3] *= -1
                  bm = bm.toMat43()
                  bs.writeFloat(bm[0][0])
                  bs.writeFloat(bm[1][0])
                  bs.writeFloat(bm[2][0])
                  bs.writeFloat(bm[0][2])
                  bs.writeFloat(bm[1][2])
                  bs.writeFloat(bm[2][2])
      else:
            bs.writeInt(1)#bone count
            bs.writeInt(8)#jp name length
            bs.writeBytes("\u30BB\u30F3\u30BF\u30FC".encode("utf-16-le"))#jp name
            bs.writeInt(8)#en name length
            bs.writeBytes("root".encode("utf-16-le"))#en name
            bs.writeFloat(0)#transform
            bs.writeFloat(0)
            bs.writeFloat(0)
            bs.writeByte(-1)
            bs.writeInt(0)#deform level
            bs.writeShort(26)#bone flag
            bs.writeFloat(0.0)
            bs.writeFloat(0.0)
            bs.writeFloat(0.0)

      bs.writeInt(morphCount)#morph count
      total = 0
      for mesh in mdl.meshes:
            idx = 0
            for morph in mesh.morphList:
                  bs.writeInt(len((mesh.name + "_morph" + str(idx))) * 2)#jp name length
                  bs.writeBytes((mesh.name + "_morph" + str(idx)).encode("utf-16-le"))
                  bs.writeInt(len((mesh.name + "_morph" + str(idx))) * 2)#en name length
                  bs.writeBytes((mesh.name + "_morph" + str(idx)).encode("utf-16-le"))
                  bs.writeByte(4)#morph panel
                  bs.writeByte(1)#morph type (vertex)
                  morphIdx = []
                  morphVerts = []
                  for i in range(0, len(mesh.positions)):
                        x = morph.positions[i][0] - mesh.positions[i][0]
                        y = morph.positions[i][1] - mesh.positions[i][1]
                        z = morph.positions[i][2] - mesh.positions[i][2]
                        if (x + y + z) != 0.0:
                              morphIdx.append(i + total)
                              morphVerts.append([x, y, z * -1])
                  bs.writeInt(len(morphIdx))
                  for i in range(0, len(morphIdx)):
                        if vertIdxSize == 1:
                              bs.writeByte(morphIdx[i])
                        elif vertIdxSize == 2:
                              bs.writeShort(morphIdx[i])
                        elif vertIdxSize == 4:
                              bs.writeInt(morphIdx[i])
                        bs.writeFloat(morphVerts[i][0])
                        bs.writeFloat(morphVerts[i][1])
                        bs.writeFloat(morphVerts[i][2])
                  idx += 1
            total += len(mesh.positions)
      if anim2morph:
            for morphs in animMorphs:
                  bs.writeInt(len(morphs[0]) * 2)#jp name length
                  bs.writeBytes(morphs[0].encode("utf-16-le"))
                  bs.writeInt(len(morphs[0]) * 2)#en name length
                  bs.writeBytes(morphs[0].encode("utf-16-le"))
                  bs.writeByte(4)#morph panel
                  bs.writeByte(2)#morph type (bone)
                  bs.writeInt(len(morphs[1]))
                  for bones in morphs[1]:
                        if boneIdxSize == 1:
                              bs.writeByte(bones[0])
                        elif boneIdxSize == 2:
                              bs.writeShort(bones[0])
                        elif boneIdxSize == 4:
                              bs.writeInt(bones[0])
                        bs.writeFloat(bones[1])
                        bs.writeFloat(bones[2])
                        bs.writeFloat(bones[3] * -1)
                        bs.writeBytes(bones[4].toBytes())

      bs.writeInt(3)#display count
      bs.writeInt(8)#jp name length
      bs.writeBytes("Root".encode("utf-16-le"))#jp name
      bs.writeInt(8)#en name length
      bs.writeBytes("Root".encode("utf-16-le"))#en name
      bs.writeByte(1)
      bs.writeInt(1)
      bs.writeByte(0)
      if boneIdxSize == 1:
            bs.writeByte(0)
      elif boneIdxSize == 2:
            bs.writeShort(0)
      elif boneIdxSize == 4:
            bs.writeInt(0)
      bs.writeInt(4)#jp name length
      bs.writeBytes("\u8868\u60C5".encode("utf-16-le"))#jp name
      bs.writeInt(6)#en name length
      bs.writeBytes("Exp".encode("utf-16-le"))#en name
      bs.writeByte(1)
      bs.writeInt(morphCount)
      for i in range(0, morphCount):
            bs.writeByte(1)
            if morphIdxSize == 1:
                  bs.writeByte(i)
            elif morphIdxSize == 2:
                  bs.writeShort(i)
            elif morphIdxSize == 4:
                  bs.writeInt(i)
      bs.writeInt(10)#jp name length
      bs.writeBytes("Bones".encode("utf-16-le"))#jp name
      bs.writeInt(10)#en name length
      bs.writeBytes("Bones".encode("utf-16-le"))#en name
      bs.writeByte(0)
      bs.writeInt(len(mdl.bones))
      for i in range(0, len(mdl.bones)):
            bs.writeByte(0)
            if boneIdxSize == 1:
                  bs.writeByte(i)
            elif boneIdxSize == 2:
                  bs.writeShort(i)
            elif boneIdxSize == 4:
                  bs.writeInt(i)

      bs.writeInt(0)#rigid body count

      bs.writeInt(0)#joint count
      return 1

def getIndexSize(count, sign):
      size = 1
      if sign == 0:
            if count > 32767:
                  size = 4
            elif count > 127:
                  size = 2
      elif sign == 1:
            if count > 65535:
                  size = 4
            elif count > 255:
                  size = 2
      return size

def vmdWriteAnim(anims, bs):
      if anim2morph:
            rapi.setDeferredAnims(anims)
            return 0
      else:
            anim = anims[0]
            bs.writeBytes("Vocaloid Motion Data 0002".ljust(30, chr(0)).encode("shift_jis"))#magic
            fileName = rapi.getExtensionlessName(rapi.getLocalFileName(rapi.getLastCheckedName()))
            bs.writeBytes(fileName.ljust(20, chr(0))[:20].encode("shift_jis"))#model name
            animData = [[], [], []]
            frameCount = anim.numFrames
            count = 0
            for i in range(0, frameCount):
                  for a in range(0, len(anim.bones)):
                        matrix = anim.bones[a]._matrix * anim.bones[anim.bones[a].parentIndex]._matrix.inverse()
                        if anim.bones[a].parentIndex != -1:
                              posX = anim.frameMats[count][3][0] - matrix[3][0]
                              posY = anim.frameMats[count][3][1] - matrix[3][1]
                              posZ = anim.frameMats[count][3][2] - matrix[3][2]
                        else:
                              posX = anim.frameMats[count][3][0] - anim.bones[a]._matrix[3][0]
                              posY = anim.frameMats[count][3][1] - anim.bones[a]._matrix[3][1]
                              posZ = anim.frameMats[count][3][2] - anim.bones[a]._matrix[3][2]
                        bm = anim.bones[a]._matrix.toQuat()
                        if anim.bones[a].parentIndex != -1:
                              pbm = anim.bones[anim.bones[a].parentIndex]._matrix.toQuat()
                              quat = anim.frameMats[count].toQuat() * pbm
                        else:
                              quat = anim.frameMats[count].toQuat()
                        bm[0] *= -1
                        bm[1] *= -1
                        bm[3] *= -1
                        quat[0] *= -1
                        quat[1] *= -1
                        quat[3] *= -1
                        quat = (quat.toMat43() * bm.toMat43().inverse()).toQuat()
                        test1 = [posX, posY, posZ, quat]
                        if i != frameCount - 1:
                              if anim.bones[a].parentIndex != -1:
                                    pos2X = anim.frameMats[count + 1][3][0] - matrix[3][0]
                                    pos2Y = anim.frameMats[count + 1][3][1] - matrix[3][1]
                                    pos2Z = anim.frameMats[count + 1][3][2] - matrix[3][2]
                              else:
                                    pos2X = anim.frameMats[count + 1][3][0] - anim.bones[a]._matrix[3][0]
                                    pos2Y = anim.frameMats[count + 1][3][1] - anim.bones[a]._matrix[3][1]
                                    pos2Z = anim.frameMats[count + 1][3][2] - anim.bones[a]._matrix[3][2]
                              bm2 = anim.bones[a]._matrix.toQuat()
                              if anim.bones[a].parentIndex != -1:
                                    pbm2 = anim.bones[anim.bones[a].parentIndex]._matrix.toQuat()
                                    quat2 = anim.frameMats[count].toQuat() * pbm2
                              else:
                                    quat2 = anim.frameMats[count].toQuat()
                              bm2[0] *= -1
                              bm2[1] *= -1
                              bm2[3] *= -1
                              quat2[0] *= -1
                              quat2[1] *= -1
                              quat2[3] *= -1
                              quat2 = (quat2.toMat43() * bm2.toMat43().inverse()).toQuat()
                              test2 = [pos2X, pos2Y, pos2Z, quat2]
                        if i == 0:
                              animData[0].append(anim.bones[a].name)
                              animData[1].append(i)
                              animData[2].append([posX, posY, posZ, quat])
                        elif i == frameCount - 1:
                              animData[0].append(anim.bones[a].name)
                              animData[1].append(i)
                              animData[2].append([posX, posY, posZ, quat])
                        elif test1 != animData[2][-1] and test1 != test2:
                              animData[0].append(anim.bones[a].name)
                              animData[1].append(i)
                              animData[2].append([posX, posY, posZ, quat])
                        count += 1
            bs.writeUInt(len(animData[0]))
            for i in range(len(animData[0])):
                  bs.writeBytes(animData[0][i].ljust(15, chr(0))[:15].encode("shift_jis"))
                  bs.writeUInt(animData[1][i])
                  bs.writeFloat(animData[2][i][0])
                  bs.writeFloat(animData[2][i][1])
                  bs.writeFloat(animData[2][i][2] * -1)
                  bs.writeBytes(animData[2][i][3].toBytes())
                  bs.writeBytes(bytearray.fromhex("14 14 00 00 14 14 14 14 6B 6B 6B 6B 6B 6B 6B 6B 14 14 14 14 14 14 14 6B 6B 6B 6B 6B 6B 6B 6B 00 14 14 14 14 14 14 6B 6B 6B 6B 6B 6B 6B 6B 00 00 14 14 14 14 14 6B 6B 6B 6B 6B 6B 6B 6B 00 00 00"))
            bs.writeUInt(0)
            bs.writeUInt(0)
            bs.writeUInt(0)
            bs.writeUInt(0)
            bs.writeUInt(0)
            #Sub anim export by Chrrox
            if len(anims) > 1:
                  fileName = rapi.getExtensionlessName(rapi.getLocalFileName(rapi.getLastCheckedName()))
                  for z in range(1, len(anims)):
                        writeName = rapi.getDirForFilePath(rapi.getOutputName()) + anims[z].name + ".vmd"
                        f = open(writeName, "wb")
                        print(anims[z].name)
                        anim = anims[z]
                        ex = NoeBitStream()
                        f.write("Vocaloid Motion Data 0002".ljust(30, chr(0)).encode("shift_jis"))#magic
                        f.write(fileName.ljust(20, chr(0))[:20].encode("shift_jis"))#model name
                        animData = [[], [], []]
                        frameCount = anim.numFrames
                        count = 0
                        for i in range(0, frameCount):
                              for a in range(0, len(anim.bones)):
                                    matrix = anim.bones[a]._matrix * anim.bones[anim.bones[a].parentIndex]._matrix.inverse()
                                    if anim.bones[a].parentIndex != -1:
                                          posX = anim.frameMats[count][3][0] - matrix[3][0]
                                          posY = anim.frameMats[count][3][1] - matrix[3][1]
                                          posZ = anim.frameMats[count][3][2] - matrix[3][2]
                                    else:
                                          posX = anim.frameMats[count][3][0] - anim.bones[a]._matrix[3][0]
                                          posY = anim.frameMats[count][3][1] - anim.bones[a]._matrix[3][1]
                                          posZ = anim.frameMats[count][3][2] - anim.bones[a]._matrix[3][2]
                                    bm = anim.bones[a]._matrix.toQuat()
                                    if anim.bones[a].parentIndex != -1:
                                          pbm = anim.bones[anim.bones[a].parentIndex]._matrix.toQuat()
                                          quat = anim.frameMats[count].toQuat() * pbm
                                    else:
                                          quat = anim.frameMats[count].toQuat()
                                    bm[0] *= -1
                                    bm[1] *= -1
                                    bm[3] *= -1
                                    quat[0] *= -1
                                    quat[1] *= -1
                                    quat[3] *= -1
                                    quat = (quat.toMat43() * bm.toMat43().inverse()).toQuat()
                                    test1 = [posX, posY, posZ, quat]
                                    if i != frameCount - 1:
                                          if anim.bones[a].parentIndex != -1:
                                                pos2X = anim.frameMats[count + 1][3][0] - matrix[3][0]
                                                pos2Y = anim.frameMats[count + 1][3][1] - matrix[3][1]
                                                pos2Z = anim.frameMats[count + 1][3][2] - matrix[3][2]
                                          else:
                                                pos2X = anim.frameMats[count + 1][3][0] - anim.bones[a]._matrix[3][0]
                                                pos2Y = anim.frameMats[count + 1][3][1] - anim.bones[a]._matrix[3][1]
                                                pos2Z = anim.frameMats[count + 1][3][2] - anim.bones[a]._matrix[3][2]
                                          bm2 = anim.bones[a]._matrix.toQuat()
                                          if anim.bones[a].parentIndex != -1:
                                                pbm2 = anim.bones[anim.bones[a].parentIndex]._matrix.toQuat()
                                                quat2 = anim.frameMats[count].toQuat() * pbm2
                                          else:
                                                quat2 = anim.frameMats[count].toQuat()
                                          bm2[0] *= -1
                                          bm2[1] *= -1
                                          bm2[3] *= -1
                                          quat2[0] *= -1
                                          quat2[1] *= -1
                                          quat2[3] *= -1
                                          quat2 = (quat2.toMat43() * bm2.toMat43().inverse()).toQuat()
                                          test2 = [pos2X, pos2Y, pos2Z, quat2]
                                    if i == 0:
                                          animData[0].append(anim.bones[a].name)
                                          animData[1].append(i)
                                          animData[2].append([posX, posY, posZ, quat])
                                    elif i == frameCount - 1:
                                          animData[0].append(anim.bones[a].name)
                                          animData[1].append(i)
                                          animData[2].append([posX, posY, posZ, quat])
                                    elif test1 != animData[2][-1] and test1 != test2:
                                          animData[0].append(anim.bones[a].name)
                                          animData[1].append(i)
                                          animData[2].append([posX, posY, posZ, quat])
                                    count += 1
                        f.write(struct.pack('i',len(animData[0])))
                        for i in range(len(animData[0])):
                              f.write(animData[0][i].ljust(15, chr(0))[:15].encode("shift_jis"))
                              f.write(struct.pack('i',animData[1][i]))
                              f.write(struct.pack('f',animData[2][i][0]))
                              f.write(struct.pack('f',animData[2][i][1]))
                              f.write(struct.pack('f',animData[2][i][2] * -1))
                              f.write(animData[2][i][3].toBytes())
                              f.write(bytearray.fromhex("14 14 00 00 14 14 14 14 6B 6B 6B 6B 6B 6B 6B 6B 14 14 14 14 14 14 14 6B 6B 6B 6B 6B 6B 6B 6B 00 14 14 14 14 14 14 6B 6B 6B 6B 6B 6B 6B 6B 00 00 14 14 14 14 14 6B 6B 6B 6B 6B 6B 6B 6B 00 00 00"))
                        f.write(struct.pack('5i',0,0,0,0,0))
                        f.close()
            return 1