# Copyright 2014 Gaetan Guidet
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import maya.cmds as cmds
import maya.mel as mel
from mtoa.ui.ae.shaderTemplate import ShaderAETemplate

class AEaiSeexprTemplate(ShaderAETemplate):
   
   def expressionChanged(self, nodeAttr, field):
      try:
         expr = cmds.scrollField(field, query=1, text=1)
         cmds.setAttr(nodeAttr, expr, type="string")
      except:
         pass
   
   def expressionUpdated(self, nodeAttr, field):
      try:
         cmds.scrollField(field, e=1, tx=cmds.getAttr(nodeAttr))
      except:
         pass
   
   def createExpression(self, nodeAttr):
      field = cmds.scrollField(ww=0)
      #cmds.scrollField(field, e=1, cc=lambda *args: self.expressionChanged(nodeAttr, field))
      #cmds.scrollField(field, e=1, tx=cmds.getAttr(nodeAttr))
      #
      #cmds.scriptJob(parent=field, attributeChange=(nodeAttr, lambda *args: self.expressionUpdated(nodeAttr, field)))
      self.replaceExpression(nodeAttr)
   
   def replaceExpression(self, nodeAttr):
      parent = cmds.setParent(query=1)
      children = cmds.layout(parent, query=1, childArray=1)
      
      field = parent + "|" + children[0]
      
      cmds.scrollField(field, e=1, cc=lambda *args: self.expressionChanged(nodeAttr, field))
      cmds.scrollField(field, e=1, tx=cmds.getAttr(nodeAttr))
      
      cmds.scriptJob(parent=field, replacePrevious=1, attributeChange=(nodeAttr, lambda *args: self.expressionUpdated(nodeAttr, field)))
   
   def updateVariableName(self, attr, fld):
      cmds.setAttr(attr, cmds.textField(fld, query=1, text=1), type="string")
   
   def setupVariableNameCallback(self, attr, fld):
      cmds.textField(fld, edit=1, changeCommand=lambda *args: self.updateVariableName(attr, fld))
   
   def updateFloatVariableValue(self, attr, fld):
      cmds.setAttr(attr, cmds.floatField(fld, query=1, value=1))
   
   def updateFloatVariableConnectivity(self, attr, fld):
      conn = (cmds.listConnections(attr, s=1, d=0) is not None)
      # (0.871, 0.447, 0.478) => animation
      # (0.945, 0.945, 0.647) => other connections
      # (0.165, 0.165, 0.165) => editable
      if conn:
         cmds.floatField(fld, edit=1, editable=False, backgroundColor=(0.945, 0.945, 0.647))
      else:
         cmds.floatField(fld, edit=1, editable=True, backgroundColor=(0.165, 0.165, 0.165))
   
   def setupFloatVariableValueCallback(self, attr, fld):
      cmds.floatField(fld, edit=1, changeCommand=lambda *args: self.updateFloatVariableValue(attr, fld))
      cmds.scriptJob(killWithScene=1, parent=fld, replacePrevious=True, connectionChange=(attr, lambda *args: self.updateFloatVariableConnectivity(attr, fld)))
   
   def removeFloatVariable(self, nodeAttr, varslayout, index):
      # Remove variable
      children = cmds.columnLayout(varslayout, query=1, childArray=1)
      
      if len(children) <= index:
         return
      
      baseNameAttr = nodeAttr
      baseValueAttr = nodeAttr.replace("fparam_name", "fparam_value");
      if baseValueAttr == nodeAttr:
         baseValueAttr = nodeAttr.replace("fparamName", "fparamValue")
      
      for i in xrange(index+1, len(children)):
         rembtn, namefld, _, valfld = cmds.formLayout(children[i], query=1, childArray=1)
         
         indexStr = "[%d]" % (i - 1)
         nextIndexStr = "[%d]" % i
         
         nameAttr = baseNameAttr + indexStr
         valueAttr = baseValueAttr + indexStr
         
         conns = cmds.listConnections(nameAttr, s=1, d=0, sh=1, p=1)
         if conns:
            cmds.disconnectAttr(conns[0], nameAttr)
         conns = cmds.listConnections(baseNameAttr + nextIndexStr, s=1, d=0, sh=1, p=1)
         if conns:
            cmds.connectAttr(conns[0], nameAttr)
         else:
            cmds.setAttr(nameAttr, cmds.getAttr(baseNameAttr + nextIndexStr), type="string")
         
         conns = cmds.listConnections(valueAttr, s=1, d=0, sh=1, p=1)
         if conns:
            cmds.disconnectAttr(conns[0], valueAttr)
         conns = cmds.listConnections(baseValueAttr + nextIndexStr, s=1, d=0, sh=1, p=1)
         if conns:
            cmds.connectAttr(conns[0], valueAttr)
         else:
            cmds.setAttr(valueAttr, cmds.getAttr(baseValueAttr + nextIndexStr))
         
         self.setupVariableNameCallback(nameAttr, namefld)
         self.setupFloatVariableValueCallback(valueAttr, valfld)
         self.updateFloatVariableConnectivity(valueAttr, valfld)
         
         cmds.button(rembtn, edit=1, command=lambda *args: self.removeFloatVariable(nodeAttr, varslayout, i-1))
      
      cmds.deleteUI(children[index])
      
      cmds.removeMultiInstance("%s[%d]" % (baseNameAttr, len(children)-1), b=True)
      cmds.removeMultiInstance("%s[%d]" % (baseValueAttr, len(children)-1), b=True)
   
   def addFloatVariable(self, nodeAttr, varslayout, name=None, value=None):
      n = cmds.columnLayout(varslayout, query=1, numberOfChildren=1)
      
      indexStr = "[%d]" % n
      nameAttr = nodeAttr + indexStr
      valueAttr = nodeAttr.replace("fparam_name", "fparam_value") + indexStr
      
      form = cmds.formLayout(numberOfDivisions=100, parent=varslayout)
      
      rembtn = cmds.button(label="-")
      namefld = cmds.textField(text=("fparam%d" % n if name is None else name))
      vallbl = cmds.text(label="=")
      valfld = cmds.floatField(value=(0.0 if value is None else value))
      
      if not cmds.listConnections(nameAttr, s=1, d=0):
         cmds.setAttr(nameAttr, ("fparam%d" % n if name is None else name), type="string")
      if not cmds.listConnections(valueAttr, s=1, d=0):
         cmds.setAttr(valueAttr, (0.0 if value is None else value))
      
      self.setupVariableNameCallback(nameAttr, namefld)
      self.setupFloatVariableValueCallback(valueAttr, valfld)
      self.updateFloatVariableConnectivity(valueAttr, valfld)
      
      cmds.button(rembtn, edit=1, command=lambda *args: self.removeFloatVariable(nodeAttr, varslayout, n))
      
      cmds.formLayout(form, edit=1,
                      attachForm=[(rembtn, "top", 0), (rembtn, "bottom", 0), (rembtn, "left", 0),
                                  (namefld, "top", 0), (namefld, "bottom", 0),
                                  (vallbl, "top", 0), (vallbl, "bottom", 0),
                                  (valfld, "top", 0), (valfld, "bottom", 0)],
                      attachControl=[(namefld, "left", 5, rembtn),
                                     (vallbl, "left", 5, namefld),
                                     (valfld, "left", 5, vallbl)],
                      attachNone=[(rembtn, "right"),
                                  (vallbl, "right")],
                      attachPosition=[(namefld, "right", 0, 30),
                                      (valfld, "right", 0, 100)])
   
   def updateVectorVariableValue(self, attr, fld0, fld1, fld2):
      x = cmds.floatField(fld0, query=1, value=1)
      y = cmds.floatField(fld1, query=1, value=1)
      z = cmds.floatField(fld2, query=1, value=1)
      #cmds.setAttr(attr, x, y, z);
      if cmds.listConnections(attr+".vparamValueX", s=1, d=0) is None:
         cmds.setAttr(attr+".vparamValueX", x)
      if cmds.listConnections(attr+".vparamValueY", s=1, d=0) is None:
         cmds.setAttr(attr+".vparamValueY", y)
      if cmds.listConnections(attr+".vparamValueZ", s=1, d=0) is None:
         cmds.setAttr(attr+".vparamValueZ", z)
   
   def updateVectorVariableConnectivity(self, attr, fld0, fld1, fld2):
      xconn = (cmds.listConnections(attr+".vparamValueX", s=1, d=0) is not None)
      yconn = (cmds.listConnections(attr+".vparamValueY", s=1, d=0) is not None)
      zconn = (cmds.listConnections(attr+".vparamValueZ", s=1, d=0) is not None)
      fullconn = (cmds.listConnections(attr, s=1, d=0) is not None)
      # (0.871, 0.447, 0.478) => animation
      # (0.945, 0.945, 0.647) => other connections
      # (0.165, 0.165, 0.165) => editable
      if xconn or fullconn:
         cmds.floatField(fld0, edit=1, editable=False, backgroundColor=(0.945, 0.945, 0.647))
      else:
         cmds.floatField(fld0, edit=1, editable=True, backgroundColor=(0.165, 0.165, 0.165))
      if yconn or fullconn:
         cmds.floatField(fld1, edit=1, editable=False, backgroundColor=(0.945, 0.945, 0.647))
      else:
         cmds.floatField(fld1, edit=1, editable=True, backgroundColor=(0.165, 0.165, 0.165))
      if zconn or fullconn:
         cmds.floatField(fld2, edit=1, editable=False, backgroundColor=(0.945, 0.945, 0.647))
      else:
         cmds.floatField(fld2, edit=1, editable=True, backgroundColor=(0.165, 0.165, 0.165))
   
   def setupVectorVariableValueCallback(self, attr, fld0, fld1, fld2):
      cmds.floatField(fld0, edit=1, changeCommand=lambda *args: self.updateVectorVariableValue(attr, fld0, fld1, fld2))
      cmds.floatField(fld1, edit=1, changeCommand=lambda *args: self.updateVectorVariableValue(attr, fld0, fld1, fld2))
      cmds.floatField(fld2, edit=1, changeCommand=lambda *args: self.updateVectorVariableValue(attr, fld0, fld1, fld2))
      cmds.scriptJob(killWithScene=1, parent=fld0, replacePrevious=True, connectionChange=(attr, lambda *args: self.updateVectorVariableConnectivity(attr, fld0, fld1, fld2)))
   
   def removeVectorVariable(self, nodeAttr, varslayout, index):
      children = cmds.columnLayout(varslayout, query=1, childArray=1)
      
      if len(children) <= index:
         return
      
      baseNameAttr = nodeAttr
      baseValueAttr = nodeAttr.replace("vparam_name", "vparam_value")
      if baseValueAttr == nodeAttr:
         baseValueAttr = nodeAttr.replace("vparamName", "vparamValue")
      
      for i in xrange(index+1, len(children)):
         #rembtn, namefld, _, val0fld, val1fld, val2fld = cmds.formLayout(children[i], query=1, childArray=1)
         rembtn, namefld, _, val0fld, val1fld, val2fld = cmds.formLayout(children[i-1], query=1, childArray=1)
         
         indexStr = "[%d]" % (i - 1)
         nextIndexStr = "[%d]" % i
         
         nameAttr = baseNameAttr + indexStr
         valueAttr = baseValueAttr + indexStr
         
         # Disconnect target attribute
         conns = cmds.listConnections(nameAttr, s=1, d=0, sh=1, p=1)
         if conns:
            cmds.disconnectAttr(conns[0], nameAttr)
         # Set or connect target attribute
         conns = cmds.listConnections(baseNameAttr + nextIndexStr, s=1, d=0, sh=1, p=1)
         if conns:
            cmds.connectAttr(conns[0], nameAttr)
         else:
            cmds.setAttr(nameAttr, cmds.getAttr(baseNameAttr + nextIndexStr), type="string")
         
         # Disconnect target attribute
         conns = cmds.listConnections(valueAttr, s=1, d=0, sh=1, p=1)
         if conns:
            cmds.disconnectAttr(conns[0], valueAttr)
         for sub in (".vparamValueX", ".vparamValueY", ".vparamValueZ"):
            conns = cmds.listConnections(valueAttr + sub, s=1, d=0, sh=1, p=1)
            if conns:
               cmds.disconnectAttr(conns[0], valueAttr + sub)
         # Set or connect target attribute components
         value = cmds.getAttr(baseValueAttr + nextIndexStr)[0]
         for sub, val in ((".vparamValueX", value[0]), (".vparamValueY", value[1]), (".vparamValueZ", value[2])):
            conns = cmds.listConnections(baseValueAttr + nextIndexStr + sub, s=1, d=0, sh=1, p=1)
            if conns:
               cmds.connectAttr(conns[0], valueAttr + sub)
            else:
               cmds.setAttr(valueAttr + sub, val)
         # Connect target attribute as a whole
         conns = cmds.listConnections(baseValueAttr + nextIndexStr, s=1, d=0, sh=1, p=1)
         if conns:
            cmds.connectAttr(conns[0], valueAttr)
         #cmds.setAttr(valueAttr, *value);
         
         # => must update remove callback
         
         self.setupVariableNameCallback(nameAttr, namefld)
         self.setupVectorVariableValueCallback(valueAttr, val0fld, val1fld, val2fld)
         self.updateVectorVariableConnectivity(valueAttr, val0fld, val1fld, val2fld)
         
         cmds.button(rembtn, edit=1, command=lambda *args: self.removeVectorVariable(nodeAttr, varslayout, i-1))
      
      cmds.deleteUI(children[index])
      
      cmds.removeMultiInstance("%s[%d]" % (baseNameAttr, len(children)-1), b=True)
      cmds.removeMultiInstance("%s[%d]" % (baseValueAttr, len(children)-1), b=True)
   
   def addVectorVariable(self, nodeAttr, varslayout, name=None, value=None):
      n = cmds.columnLayout(varslayout, query=1, numberOfChildren=1)
      
      indexStr = "[%d]" % n
      nameAttr = nodeAttr + indexStr
      valueAttr = nodeAttr.replace("vparam_name", "vparam_value") + indexStr
      
      if value is None:
         value = (0.0, 0.0, 0.0)
      else:
         value = value[0]
      
      form = cmds.formLayout(numberOfDivisions=100, parent=varslayout)
      
      rembtn = cmds.button(label="-")
      namefld = cmds.textField(text=("vparam%d" % n if name is None else name))
      vallbl = cmds.text(label="=")
      val0fld = cmds.floatField(value=value[0])
      val1fld = cmds.floatField(value=value[1])
      val2fld = cmds.floatField(value=value[2])
      
      if not cmds.listConnections(nameAttr, s=1, d=0):
         cmds.setAttr(nameAttr, ("vparam%d" % n if name is None else name), type="string")
      #cmds.setAttr(valueAttr, *value)
      if not cmds.listConnections(valueAttr, s=1, d=0):
         # not fully connected, but could still be connected at component level
         if not cmds.listConnections(valueAttr+".vparamValueX", s=1, d=0):
            cmds.setAttr(valueAttr+".vparamValueX", value[0])
         if not cmds.listConnections(valueAttr+".vparamValueY", s=1, d=0):
            cmds.setAttr(valueAttr+".vparamValueY", value[1])
         if not cmds.listConnections(valueAttr+".vparamValueZ", s=1, d=0):
            cmds.setAttr(valueAttr+".vparamValueZ", value[1])
      
      self.setupVariableNameCallback(nameAttr, namefld)
      self.setupVectorVariableValueCallback(valueAttr, val0fld, val1fld, val2fld)
      self.updateVectorVariableConnectivity(valueAttr, val0fld, val1fld, val2fld)
      cmds.button(rembtn, edit=1, command=lambda *args: self.removeVectorVariable(nodeAttr, varslayout, n))
      
      cmds.formLayout(form, edit=1,
                      attachForm=[(rembtn, "top", 0), (rembtn, "bottom", 0), (rembtn, "left", 0),
                                  (namefld, "top", 0), (namefld, "bottom", 0),
                                  (vallbl, "top", 0), (vallbl, "bottom", 0),
                                  (val0fld, "top", 0), (val0fld, "bottom", 0),
                                  (val1fld, "top", 0), (val1fld, "bottom", 0),
                                  (val2fld, "top", 0), (val2fld, "bottom", 0)],
                      attachControl=[(namefld, "left", 5, rembtn),
                                     (vallbl, "left", 5, namefld),
                                     (val0fld, "left", 5, vallbl),
                                     (val1fld, "left", 5, val0fld),
                                     (val2fld, "left", 5, val1fld)],
                      attachNone=[(rembtn, "right"),
                                  (vallbl, "right")],
                      attachPosition=[(namefld, "right", 0, 30),
                                      (val0fld, "right", 0, 53),
                                      (val1fld, "right", 0, 76),
                                      (val2fld, "right", 0, 100)])
   
   def removeAllVariables(self, nodeAttr, varslayout):
      nameAttr = nodeAttr
      
      valueAttr = nodeAttr.replace("fparam_name", "fparam_value")
      if valueAttr == nameAttr:
         valueAttr = nameAttr.replace("vparam_name", "vparam_value")
      
      indices = cmds.getAttr(nameAttr, multiIndices=1)
      for index in indices:
         cmds.removeMultiInstance("%s[%d]" % (nameAttr, index), b=True)
      
      indices = cmds.getAttr(valueAttr, multiIndices=1)
      for index in indices:
         cmds.removeMultiInstance("%s[%d]" % (valueAttr, index), b=True)
      
      children = cmds.columnLayout(varslayout, query=1, childArray=1)
      for child in children:
         cmds.deleteUI(child)
   
   def syncFloatVariable(self, nameAttr, valueAttr, idx, layout):
      elemNameAttr = "%s[%d]" % (nameAttr, idx)
      elemValueAttr = "%s[%d]" % (valueAttr, idx)
      
      topLayout = cmds.formLayout(layout, query=1, parent=1)
      children = cmds.formLayout(layout, query=1, childArray=1)
      
      cmds.textField(children[1], edit=1, text=cmds.getAttr(elemNameAttr))
      cmds.floatField(children[3], edit=1, value=cmds.getAttr(elemValueAttr))
      
      self.setupVariableNameCallback(elemNameAttr, children[1])
      self.setupFloatVariableValueCallback(elemValueAttr, children[3])
      self.updateFloatVariableConnectivity(elemValueAttr, children[3])
      cmds.button(children[0], edit=1, command=lambda *args: self.removeFloatVariable(nameAttr, topLayout, idx))
   
   def syncVectorVariable(self, nameAttr, valueAttr, idx, layout):
      elemNameAttr = "%s[%d]" % (nameAttr, idx)
      elemValueAttr = "%s[%d]" % (valueAttr, idx)

      topLayout = cmds.formLayout(layout, query=1, parent=1)
      children = cmds.formLayout(layout, query=1, childArray=1)
      
      value = cmds.getAttr(elemValueAttr)
      value = value[0]
      
      cmds.textField(children[1], edit=1, text=cmds.getAttr(elemNameAttr))
      cmds.floatField(children[3], edit=1, value=value[0])
      cmds.floatField(children[4], edit=1, value=value[1])
      cmds.floatField(children[5], edit=1, value=value[2])

      self.setupVariableNameCallback(elemNameAttr, children[1])
      self.setupVectorVariableValueCallback(elemValueAttr, children[3], children[4], children[5])
      self.updateVectorVariableConnectivity(elemValueAttr, children[3], children[4], children[5])
      cmds.button(children[0], edit=1, command=lambda *args: self.removeVectorVariable(nameAttr, topLayout, idx))
   
   def syncNameValueArrays(self, nameAttr, valueAttr, vectorValues=False):
      count0 = cmds.getAttr(nameAttr, size=1)
      count1 = cmds.getAttr(valueAttr, size=1)
      
      count = (count0 if count0 < count1 else count1)
      
      indices0 = cmds.getAttr(nameAttr, multiIndices=1)
      indices1 = cmds.getAttr(valueAttr, multiIndices=1)
      
      if count0 > count1:
         for i in xrange(count1, count0):
            cmds.removeMultiInstance("%s[%d]" % (nameAttr, indices0[i]), b=True)
         indices0 = indices0[0:count1]
         
      elif count1 > count0:
         for i in xrange(count0, count1):
            cmds.removeMultiInstance("%s[%d]" % (valueAttr, indices1[i]), b=True)
         indices1 = indices1[0:count0]
      
      reorder = False
      for i in xrange(count):
         if indices0[i] != i or indices1[i] != i:
            reorder = True
            break
      
      if reorder:
         vl = []
         rl0 = set()
         rl1 = set()
         
         # Get current name/value pairs and list indices beyond count
         for i in xrange(count):
            vl.append((cmds.getAttr("%s[%d]" % (nameAttr, indices0[i])),
                       cmds.getAttr("%s[%d]" % (valueAttr, indices1[i]))))
            
            if indices0[i] >= count:
               rl0.add(indices0[i])
            
            if indices1[i] >= count:
               rl0.add(indices1[i])
         
         for i in xrange(count):
            k, v = vl[i]
            cmds.setAttr("%s[%d]" % (nameAttr, i), k, type="string")
            if vectorValues:
               v = v[0]
               cmds.setAttr("%s[%d]" % (valueAttr, i), *v)
            else:
               cmds.setAttr("%s[%d]" % (valueAttr, i), v)
         
         for i in rl0:
            cmds.removeMultiInstance("%s[%d]" % (nameAttr, i), b=True)
         
         for i in rl1:
            cmds.removeMultiInstance("%s[%d]" % (valueAttr, i), b=True)
      
      return count
   
   def createFloatVariables(self, nodeAttr):
      form = cmds.formLayout(numberOfDivisions=100)
      
      btnrow = cmds.rowLayout(numberOfColumns=2)
      addbtn = cmds.button(label="Add New")
      rembtn = cmds.button(label="Remove All")
      cmds.setParent("..")
      
      varslayout = cmds.columnLayout(rowSpacing=5, adjustableColumn=True, columnAttach=("both", 5))
      cmds.setParent("..")
      
      cmds.formLayout(form, edit=1,
                      attachForm=[(btnrow, "top", 5),
                                  (btnrow, "left", 5),
                                  (btnrow, "right", 5),
                                  (varslayout, "left", 5),
                                  (varslayout, "right", 5)],
                      attachControl=[(varslayout, "top", 5, btnrow)],
                      attachNone=[(btnrow, "bottom"),
                                  (varslayout, "bottom")])
      
      cmds.setParent("..")
      
      self.replaceFloatVariables(nodeAttr)
   
   def replaceFloatVariables(self, nodeAttr):
      parent = cmds.setParent(query=1)
      children = cmds.layout(parent, query=1, childArray=1)
      
      form = parent + "|" + children[0]
      children = cmds.layout(form, query=1, childArray=1)
      
      rowlayout = form + "|" + children[0]
      varslayout = form + "|" + children[1]
      
      children = cmds.layout(rowlayout, query=1, childArray=1)
      
      addbtn = rowlayout + "|" + children[0]
      rembtn = rowlayout + "|" + children[1]
      
      cmds.button(addbtn, edit=1, command=lambda *args: self.addFloatVariable(nodeAttr, varslayout))
      cmds.button(rembtn, edit=1, command=lambda *args: self.removeAllVariables(nodeAttr, varslayout))
      
      # Update content
      nameAttr = nodeAttr
      valueAttr = nodeAttr.replace("fparam_name", "fparam_value")
      
      # Sync name/value arrays
      count = self.syncNameValueArrays(nameAttr, valueAttr, vectorValues=False)
      
      # Build UI
      children = cmds.columnLayout(varslayout, query=1, childArray=1)
      if children is None:
         children = []
      uicount = len(children)
      
      # Remove extra variables
      while uicount > count:
         cmds.deleteUI(children[-1])
         uicount -= 1
      
      # Sync existing values
      for i in xrange(uicount):
         self.syncFloatVariable(nameAttr, valueAttr, i, children[i])
      
      # Add missing variables
      while uicount < count:
         self.addFloatVariable(nodeAttr, varslayout,
                               name=cmds.getAttr("%s[%d]" % (nameAttr, uicount)),
                               value=cmds.getAttr("%s[%d]" % (valueAttr, uicount)))
         uicount += 1
   
   def createVectorVariables(self, nodeAttr):
      form = cmds.formLayout(numberOfDivisions=100)
      
      btnrow = cmds.rowLayout(numberOfColumns=2)
      addbtn = cmds.button(label="Add New")
      rembtn = cmds.button(label="Remove All")
      cmds.setParent("..")
      
      varslayout = cmds.columnLayout(rowSpacing=5, adjustableColumn=True, columnAttach=("both", 5))
      cmds.setParent("..")
      
      cmds.formLayout(form, edit=1,
                      attachForm=[(btnrow, "top", 5),
                                  (btnrow, "left", 5),
                                  (btnrow, "right", 5),
                                  (varslayout, "left", 5),
                                  (varslayout, "right", 5)],
                      attachControl=[(varslayout, "top", 5, btnrow)],
                      attachNone=[(btnrow, "bottom"),
                                  (varslayout, "bottom")])
      
      cmds.setParent("..")
      
      self.replaceVectorVariables(nodeAttr)
   
   def replaceVectorVariables(self, nodeAttr):
      parent = cmds.setParent(query=1)
      children = cmds.layout(parent, query=1, childArray=1)
      
      form = parent + "|" + children[0]
      children = cmds.layout(form, query=1, childArray=1)
      
      rowlayout = form + "|" + children[0]
      varslayout = form + "|" + children[1]
      
      children = cmds.layout(rowlayout, query=1, childArray=1)
      
      addbtn = rowlayout + "|" + children[0]
      rembtn = rowlayout + "|" + children[1]
      
      cmds.button(addbtn, edit=1, command=lambda *args: self.addVectorVariable(nodeAttr, varslayout))
      cmds.button(rembtn, edit=1, command=lambda *args: self.removeAllVariables(nodeAttr, varslayout))
      
      # Update content
      nameAttr = nodeAttr
      valueAttr = nodeAttr.replace("vparam_name", "vparam_value")
      
      # Sync name/value arrays
      count = self.syncNameValueArrays(nameAttr, valueAttr, vectorValues=True)
      
      # Build UI
      children = cmds.columnLayout(varslayout, query=1, childArray=1)
      if children is None:
         children = []
      uicount = len(children)
      
      # Remove extra variables
      while uicount > count:
         cmds.deleteUI(children[-1])
         uicount -= 1
      
      # Sync existing values
      for i in xrange(uicount):
         self.syncVectorVariable(nameAttr, valueAttr, i, children[i])
      
      # Add missing variables
      while uicount < count:
         self.addVectorVariable(nodeAttr, varslayout,
                               name=cmds.getAttr("%s[%d]" % (nameAttr, uicount)),
                               value=cmds.getAttr("%s[%d]" % (valueAttr, uicount)))
         uicount += 1
   
   def setup(self):
      self.addSwatch()
      
      self.beginScrollLayout()
      
      self.beginLayout("Expression", collapse=False)
      self.addCustom('expression', self.createExpression, self.replaceExpression)
      self.endLayout()
      
      self.beginLayout("Float variables", collapse=False)
      self.addCustom('fparam_name', self.createFloatVariables, self.replaceFloatVariables)
      self.suppress('fparam_value')
      self.endLayout()
      
      self.beginLayout("Vector variables", collapse=False)
      self.addCustom('vparam_name', self.createVectorVariables, self.replaceVectorVariables)
      self.suppress('vparam_value')
      self.endLayout()
      
      self.addControl('stop_on_error', label="Stop On Error")
      self.addControl('error_value', label="Error Value")
      
      mel.eval('AEdependNodeTemplate("%s")' % self.nodeName)
      self.addExtraControls()
      self.endScrollLayout()
   
