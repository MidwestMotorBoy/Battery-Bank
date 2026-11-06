"""Import the Monolith part STEPs (hardware/mechanical/step/monolith-step-files.zip, unzipped) into the active Fusion design
as reference components, one per file, in the pack frame, with the STEP colours. Fusion scripts run inside a command, where
ImportManager.importToTarget fails, so each file goes to a new document (importToNewDocument), its bodies are copied
across with TemporaryBRepManager and the import document is closed unsaved. Set D to the unzipped parts/ folder and FILES
to the part files to bring in; the board (09_board_kicad.step) takes ~45 s and comes in as 1,152 unnamed bodies."""
import adsk.core, adsk.fusion, os, time

D = os.path.join(os.path.expanduser('~'), 'monolith_step', 'parts')   # where you unzipped monolith-step-files.zip
FILES = ['01_carrier.step', '02_board_rails.step', '03_cells_C1-C4.step', '09_board_kicad.step', '11_cup.step', '14_cap.step']


def design_of(doc):
    return adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))


def run(_context: str):
    app = adsk.core.Application.get()
    tbm = adsk.fusion.TemporaryBRepManager.get()
    main = app.activeDocument                      # the parts go into the design that is active when the script starts
    for f in FILES:
        t = time.time()
        opt = app.importManager.createSTEPImportOptions(os.path.join(D, f))
        src = app.importManager.importToNewDocument(opt)
        sdes = design_of(src)
        sroot = sdes.rootComponent
        items = []                                       # (name, temp body, appearance name)
        for b in sroot.bRepBodies:
            items.append((b.name, tbm.copy(b), b.appearance))
        for oc in sroot.allOccurrences:
            for b in oc.component.bRepBodies:
                p = b.createForAssemblyContext(oc)
                items.append((oc.name.split(':')[0] + '/' + b.name, tbm.copy(p), b.appearance))
        apps = {}
        for _, _, a in items:
            if a and a.name not in apps:
                apps[a.name] = a
        main.activate()
        mdes = design_of(main)
        root = mdes.rootComponent
        if mdes.designIntent != adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
            mdes.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType
        for n, a in apps.items():
            if not mdes.appearances.itemByName(n):
                try:
                    mdes.appearances.addByCopy(a, n)
                except Exception:
                    pass
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = os.path.splitext(f)[0]
        bf = comp.features.baseFeatures.add()
        bf.startEdit()
        for n, tb, a in items:
            nb = comp.bRepBodies.add(tb, bf)
            nb.name = n[:60]
            if a and mdes.appearances.itemByName(a.name):
                nb.appearance = mdes.appearances.itemByName(a.name)
        bf.finishEdit()
        src.close(False)
        vol, bad = 0.0, 0
        for b in comp.bRepBodies:
            try:
                vol += b.volume * 1000.0 if b.isSolid else 0.0
                bad += 0 if b.isSolid else 1
            except Exception:
                bad += 1
        print('%s: %d bodies (%d open/unmeasurable), %.1f mm3, %.1fs' % (f, comp.bRepBodies.count, bad, vol, time.time() - t))
