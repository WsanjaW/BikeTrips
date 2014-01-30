var open = 1;
function addfileform()
{
    if(open==0){
        document.getElementById("contact_form").style.display='none'; 
        open=1;
    }
    else
    {
        document.getElementById("contact_form").style.display='block';
        open=0;
    }
}