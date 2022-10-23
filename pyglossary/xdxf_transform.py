from pyglossary import core
from pyglossary.core import rootDir
import logging
from io import BytesIO
from io import StringIO

log = logging.getLogger("pyglossary")


class XdxfTransformer(object):
	_gram_color: str = "green"
	_example_padding: int = 10

	def __init__(self, encoding="utf-8"):
		self._encoding = encoding

	def tostring(self, elem: "lxml.etree.Element") -> str:
		from lxml import etree as ET
		return ET.tostring(
			elem,
			method="html",
			pretty_print=True,
		).decode("utf-8").strip()

	def hasPrevText(self, prev: "Union[None, str, lxml.etree.Element]"):
		if isinstance(prev, str):
			return True
		if prev is None:
			return False
		if prev.tag == "k":
			return False
		if prev.tag in (
			"dtrn", "def", "span", "co",
			"i", "b", "sub", "sup", "tt", "big", "small",
		):
			return True
		if prev.text:
			return True
		# print(prev)
		return False

	def writeString(
		self,
		hf: "lxml.etree.htmlfile",
		child: str,
		parent: "lxml.etree.Element",
		prev: "Union[None, str, lxml.etree.Element]",
		stringSep: "Optional[str]" = None,
	):
		from lxml import etree as ET

		def addSep():
			if stringSep is None:
				hf.write(ET.Element("br"))
			else:
				hf.write(stringSep)

		hasPrev = self.hasPrevText(prev)
		trail = False
		if parent.tag in ("ar", "font"):
			if child.startswith("\n"):
				child = child.lstrip("\n")
				if hasPrev:
					hf.write(ET.Element("br"))
			elif child.endswith("\n"):
				child = child.rstrip("\n")
				trail = True
			if not hasPrev:
				child = child.lstrip()
		elif child.startswith("\n"):
			child = child.lstrip()
			if hasPrev:
				addSep()

		child = child.rstrip()
		lines = [line for line in child.split("\n") if line]
		# parentTransparent = parent.tag in ("b", "i", "u", "c", "kref")
		for index, line in enumerate(lines):
			#print(f"{index=}, {line=}, {parent=}, {prev=}")
			#if index > 0 or parentTransparent:
				# and line[0] not in ".,;)"
			addSep()
			hf.write(line)
		if trail:
			addSep()
		return

	def writeExample(
		self,
		hf: "lxml.etree.htmlfile",
		elem: "Union[str, lxml.etree.Element]",
	):
		prev = None
		stringSep = " "
		with hf.element("div", **{
			"class": "example",
			"style": f"padding: {self._example_padding}px 0px;",
		}):
			for child in elem.xpath("child::node()"):
				if isinstance(child, str):
					# if not child.strip():
					# 	continue
					self.writeString(hf, child, elem, prev, stringSep=stringSep)
					continue
				if child.tag == "iref":
					with hf.element("div"):
						self.writeIRef(hf, child)
					continue
				if child.tag in ("ex_orig", "ex_tran"):
					with hf.element("div"):
						self.writeChildrenOf(hf, child, stringSep=stringSep)
					continue
				# log.warning(f"unknown tag {child.tag} inside <ex>")
				self.writeChild(hf, child, elem, prev, stringSep=stringSep)
				prev = child

	def writeIRef(
		self,
		hf: "lxml.etree.htmlfile",
		child: "Union[str, lxml.etree.Element]",
	):
		iref_url = child.attrib.get("href", "")
		if any(iref_url.endswith(ext) for ext in ("mp3", "wav", "aac", "ogg")):
			#  with hf.element("audio", src=iref_url):
			with hf.element("a", **{
				"class": "iref",
				"href": iref_url,
			}):
				hf.write("🔊")
			return
		else:
			with hf.element("a", **{
				"class": "iref",
				"href": child.attrib.get("href", child.text),
			}):
				self.writeChildrenOf(hf, child, stringSep=" ")

	def writeChild(
		self,
		hf: "lxml.etree.htmlfile",
		child: "Union[str, lxml.etree.Element]",
		parent: "lxml.etree.Element",
		prev: "Union[None, str, lxml.etree.Element]",
		stringSep: "Optional[str]" = None,
	):
		from lxml import etree as ET

		if isinstance(child, str):
			if not child.strip():
				return
			self.writeString(hf, child, parent, prev, stringSep=stringSep)
			return

		if child.tag == f"br":
			hf.write(ET.Element("br"))
			return

		if child.tag in ("i", "b", "sub", "sup", "tt", "big", "small"):
			with hf.element(child.tag):
				self.writeChildrenOf(hf, child)
				# if child.text is not None:
				# 	hf.write(child.text.strip("\n"))
			return

		if child.tag == "blockquote":
			with hf.element("div", **{"class": "m"}):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "tr":
			hf.write("[")
			self.writeChildrenOf(hf, child)
			hf.write("]")
			hf.write(ET.Element("br"))
			return

		if child.tag == "k":
			with hf.element("div", **{"class": child.tag}):
				# with glos.titleElement(hf, child.text):
				# ^ no glos object here!
				with hf.element("b"):
					self.writeChildrenOf(hf, child)
			return

		if child.tag == "sr":
			with hf.element("div", **{"class": child.tag}):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "ex":
			self.writeExample(hf, child)
			return

		if child.tag == "mrkd":
			if not child.text:
				return
			with hf.element("span", **{"class": child.tag}):
				with hf.element("b"):
					hf.write(child.text)
			return

		if child.tag in ("pos", "abr"):
			with hf.element("span", **{"class": "abr"}):
				with hf.element("font", color="green"):
					with hf.element("i"):
						self.writeChildrenOf(hf, child)
			return

		if child.tag == "co":
			with hf.element("div"):
				self.writeChildrenOf(hf, child, sep=" ")
			return

		if child.tag == "dtrn":
			self.writeChildrenOf(hf, child, sep=" ")
			return

		if child.tag == "c":
			color = child.attrib.get("c", "green")
			with hf.element("font", color=color):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "kref":
			if not child.text:
				log.warning(f"kref with no text: {self.tostring(child)}")
				return
			with hf.element("a", **{
				"class": "kref",
				"href": f"bword://{child.attrib.get('k', child.text)}",
			}):
				hf.write(child.text)
			return

		if child.tag == "iref":
			self.writeIRef(hf, child)
			return

		if child.tag == "rref":
			if not child.text:
				log.warning(f"rref with no text: {self.tostring(child)}")
				return

		if child.tag == "def":
			# TODO: create a list (ol / ul) unless it has one item only
			# like FreeDict reader
			with hf.element("div"):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "deftext":
			self.writeChildrenOf(hf, child, stringSep=" ", sep=" ")
			return

		if child.tag == "span":
			with hf.element("span"):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "abbr_def":
			# _type = child.attrib.get("type", "")
			# {"": "", "grm": "grammatical", "stl": "stylistical",
			#  "knl": "area/field of knowledge", "aux": "subsidiary"
			#  "oth": "others"}[_type]
			self.writeChildrenOf(hf, child)
			return

		if child.tag == "gr":
			with hf.element("font", color=self._gram_color):
				hf.write(child.text)
			hf.write(ET.Element("br"))
			return

		if child.tag == "ex_orig":
			with hf.element("i"):
				self.writeChildrenOf(hf, child)
			return

		if child.tag == "ex_transl" and prev.tag == "ex_orig":
			if child.text != prev.text:
				with hf.element("i"):
					self.writeChildrenOf(hf, child)
			return

		if child.tag == "categ":  # Category
			with hf.element("span", style="background-color: green;"):
				self.writeChildrenOf(hf, child, stringSep=" ")
			return

		if child.tag == "opt":
			if child.text:
				hf.write(" (")
				hf.write(child.text)
				hf.write(")")
			return

		if child.tag == "img":
			with hf.element("img", **child.attrib):
				pass
			return

		if child.tag == "abbr":
			# FIXME: may need an space or newline before it
			with hf.element("i"):
				hf.write(f"{child.text}")
			return

		if child.tag == "etm":  # Etymology (history and origin)
			# TODO: formatting?
			hf.write(f"{child.text}")
			return

		log.warning(f"unknown tag {child.tag}")
		self.writeChildrenOf(hf, child)

	def shouldAddSep(
		self,
		child: "Union[str, lxml.etree.Element]",
		prev: "Union[str, lxml.etree.Element]",
	):
		if isinstance(child, str):
			if len(child) > 0 and child[0] in ".,;)":
				return False
			return True

		if child.tag in ("sub", "sup"):
			return False

		if isinstance(prev, str):
			pass
		elif prev.tag in ("sub", "sup"):
			return False

		return True

	def writeChildrenOf(
		self,
		hf: "lxml.etree.htmlfile",
		elem: "lxml.etree.Element",
		sep: "Optional[str]" = None,
		stringSep: "Optional[str]" = None,
	):
		prev = None
		for index, child in enumerate(elem.xpath("child::node()")):
			if sep and index > 0 and self.shouldAddSep(child, prev):
				hf.write(sep)
			self.writeChild(hf, child, elem, prev, stringSep=stringSep)
			prev = child

	def transform(self, article: "lxml.etree.Element") -> str:
		from lxml import etree as ET
		encoding = self._encoding
		f = BytesIO()
		with ET.htmlfile(f, encoding="utf-8") as hf:
			with hf.element("div", **{"class": "article"}):
				self.writeChildrenOf(hf, article)

		text = f.getvalue().decode("utf-8")
		text = text.replace("<br>", "<br/>")  # for compatibility
		return text

	def transformByInnerString(self, articleInnerStr: str) -> str:
		from lxml import etree as ET
		return self.transform(
			ET.fromstring(f"<ar>{articleInnerStr}</ar>")
		)
