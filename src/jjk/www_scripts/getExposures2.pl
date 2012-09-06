#!/usr/bin/env perl 
## get the list of LS-VW expousres.. insert entries in the LSVW mysql DB on cadchd.


use Net::MySQL;
#use Bucket::MOP;
use strict;
use warnings;
use Term::ReadKey;


my $hostname="cadchd.hia.nrc.ca";
my $port=33306;
my $database="bucket";
my $user="lsadmin";
my $password="";

### Try and open the .dbrc file and get the needed information
open (DBRC,"< /home/cadc/kavelaar/.dbrc ");
while (<DBRC>) { 
	my ( $type, $db, $db_user, $db_password ) = split ;
	chomp $db_password;
	$password = $db_password;
	last if ( $db_user =~ m/$user/ && $db =~ m/$database/ && $type =~ m/MYSQL/ ) ;
	$password='';
}
	
if ( ! $password ) { 
print STDERR "Please enter the DB password for $user on $hostname: ";

ReadMode 3; 
$password=<STDIN>;
chomp $password; 
print "\n"; 
ReadMode 1;

chomp $password;
}


my $mysql = Net::MySQL->new(
			    hostname => $hostname,
			    port => $port,
			    database => $database,
			    user => $user,
			    password => $password
			    ) ||die "Cann't connect to DB";

my @cols=("expnum","object","ra","dec","exptime","mjdate","filter","runid","qrunid","date","uttime");



### get the list of exposures from the CADC and insert them into the db
print STDERR "Getting exposure table from CADC\n";
open(EXP,"curl -s http://cadc.hia.nrc.ca/cadcbin/cfhtlsvw/exposure.pl | ");
print STDERR "Scanning list for new exposures \n";
while (<EXP>) {
    my @values=split;
    
    my $expnum = $values[0];
    my $mjdate = $values[5]; 
    print STDERR "checking if $expnum is new        ";
    ### First check if we've alread got an entry for this exposure.. if so then skip it.
    my $sql = "SELECT count(*) from exposure where expnum=$expnum ";
    $mysql->query($sql);
    die "\n Bad query $sql \n" unless  $mysql->has_selected_record;
    my $rec_set = $mysql->create_record_iterator;
    my $count = $rec_set->each->[0];
    if ( $count > 0 ) {
	print STDERR "\r";
	next;
    }
    
    ### now add to the exposure table too.
    $sql = "INSERT INTO `exposure` (";
    my $sep = '';
    foreach my $col ( @cols ) {
	$sql .= $sep."`".$col."`";
	$sep=",";
    }
    $sep ="";
    $sql .= " ) VALUES ( " ;
    foreach my $value ( @values ) {
	$sql .= $sep."'".$value."'";
	$sep=",";
    }
    $sql .= " ) ";
    print STDERR "  Adding $values[0] \n";
    $mysql->query($sql);
    $mysql->get_affected_rows_length==1 ||die "Bad expousre insert, ($sql)\n";

}

$mysql->close;
