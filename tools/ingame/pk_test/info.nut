class PKTest extends GSInfo {
  function GetAuthor()      { return "puenktlich"; }
  function GetName()        { return "PKTest"; }
  function GetShortName()   { return "PKTT"; }
  function GetDescription() { return "Builds an electrified test loop and runs Puenktlich trains"; }
  function GetVersion()     { return 1; }
  function GetDate()        { return "2026-11-21"; }
  function CreateInstance() { return "PKTest"; }
  function GetAPIVersion()  { return "15"; }
}
RegisterGS(PKTest());
