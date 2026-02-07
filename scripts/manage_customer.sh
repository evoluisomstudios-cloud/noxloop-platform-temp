#!/bin/bash
# ============================================
# DigiForge Customer Management Script
# Usage:
#   ./manage_customer.sh info EMAIL
#   ./manage_customer.sh add-credits EMAIL AMOUNT
#   ./manage_customer.sh set-plan EMAIL PLAN
# ============================================

ACTION=$1
EMAIL=$2
PARAM=$3

show_help() {
    echo "DigiForge Customer Management"
    echo ""
    echo "Usage:"
    echo "  $0 info EMAIL                    - Show customer info"
    echo "  $0 add-credits EMAIL AMOUNT      - Add credits to customer"
    echo "  $0 set-plan EMAIL PLAN           - Set customer plan"
    echo "  $0 make-admin EMAIL              - Make user admin"
    echo "  $0 list-users                    - List all users"
    echo ""
    echo "Plans: free, starter, pro, enterprise"
    echo ""
    echo "Examples:"
    echo "  $0 info cliente@exemplo.com"
    echo "  $0 add-credits cliente@exemplo.com 100"
    echo "  $0 set-plan cliente@exemplo.com pro"
}

if [ -z "$ACTION" ]; then
    show_help
    exit 0
fi

case $ACTION in
    info)
        if [ -z "$EMAIL" ]; then
            echo "Error: EMAIL required"
            exit 1
        fi
        docker exec digiforge-mongodb mongosh digiforge --quiet --eval "
            var user = db.users.findOne({email: '$EMAIL'}, {password: 0});
            if (user) {
                print('=== User ===');
                print('ID: ' + user.user_id);
                print('Name: ' + user.name);
                print('Email: ' + user.email);
                print('Admin: ' + (user.is_admin || false));
                print('Created: ' + user.created_at);
                
                var membership = db.workspace_members.findOne({user_id: user.user_id});
                if (membership) {
                    var ws = db.workspaces.findOne({workspace_id: membership.workspace_id});
                    if (ws) {
                        print('');
                        print('=== Workspace ===');
                        print('ID: ' + ws.workspace_id);
                        print('Name: ' + ws.name);
                        print('Plan: ' + ws.plan);
                        print('Credits: ' + ws.credits);
                        print('Role: ' + membership.role);
                    }
                }
            } else {
                print('User not found: $EMAIL');
            }
        "
        ;;
        
    add-credits)
        if [ -z "$EMAIL" ] || [ -z "$PARAM" ]; then
            echo "Error: EMAIL and AMOUNT required"
            exit 1
        fi
        docker exec digiforge-mongodb mongosh digiforge --quiet --eval "
            var user = db.users.findOne({email: '$EMAIL'});
            if (user) {
                var membership = db.workspace_members.findOne({user_id: user.user_id});
                if (membership) {
                    var result = db.workspaces.updateOne(
                        {workspace_id: membership.workspace_id},
                        {\$inc: {credits: $PARAM}}
                    );
                    if (result.modifiedCount > 0) {
                        var ws = db.workspaces.findOne({workspace_id: membership.workspace_id});
                        print('✅ Added $PARAM credits to $EMAIL');
                        print('New balance: ' + ws.credits + ' credits');
                    } else {
                        print('❌ Failed to update credits');
                    }
                } else {
                    print('❌ No workspace found for user');
                }
            } else {
                print('❌ User not found: $EMAIL');
            }
        "
        ;;
        
    set-plan)
        if [ -z "$EMAIL" ] || [ -z "$PARAM" ]; then
            echo "Error: EMAIL and PLAN required"
            exit 1
        fi
        docker exec digiforge-mongodb mongosh digiforge --quiet --eval "
            var user = db.users.findOne({email: '$EMAIL'});
            if (user) {
                var membership = db.workspace_members.findOne({user_id: user.user_id});
                if (membership) {
                    var planCredits = {
                        'free': 10,
                        'starter': 50,
                        'pro': 200,
                        'enterprise': 1000
                    };
                    var credits = planCredits['$PARAM'] || 10;
                    var result = db.workspaces.updateOne(
                        {workspace_id: membership.workspace_id},
                        {\$set: {plan: '$PARAM', credits: credits}}
                    );
                    if (result.modifiedCount > 0 || result.matchedCount > 0) {
                        print('✅ Set plan \"$PARAM\" for $EMAIL');
                        print('Credits set to: ' + credits);
                    } else {
                        print('❌ Failed to update plan');
                    }
                } else {
                    print('❌ No workspace found for user');
                }
            } else {
                print('❌ User not found: $EMAIL');
            }
        "
        ;;
        
    make-admin)
        if [ -z "$EMAIL" ]; then
            echo "Error: EMAIL required"
            exit 1
        fi
        docker exec digiforge-mongodb mongosh digiforge --quiet --eval "
            var result = db.users.updateOne(
                {email: '$EMAIL'},
                {\$set: {is_admin: true}}
            );
            if (result.modifiedCount > 0) {
                print('✅ $EMAIL is now an admin');
            } else if (result.matchedCount > 0) {
                print('ℹ️ $EMAIL was already an admin');
            } else {
                print('❌ User not found: $EMAIL');
            }
        "
        ;;
        
    list-users)
        docker exec digiforge-mongodb mongosh digiforge --quiet --eval "
            print('=== All Users ===');
            db.users.find({}, {password: 0}).forEach(function(user) {
                var membership = db.workspace_members.findOne({user_id: user.user_id});
                var ws = membership ? db.workspaces.findOne({workspace_id: membership.workspace_id}) : null;
                print(user.email + ' | Plan: ' + (ws ? ws.plan : 'N/A') + ' | Credits: ' + (ws ? ws.credits : 0) + ' | Admin: ' + (user.is_admin || false));
            });
        "
        ;;
        
    *)
        show_help
        ;;
esac
